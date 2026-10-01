"""Índice local de itens e seleção de passagens literais; sem gabaritos ou IA."""
import re
import hashlib
from langchain_core.documents import Document
from .query import fold
from .storage import connect

EXPLICIT = re.compile(r"(?im)^\s*(?:\d+(?:\.\d+)+\s+)?item\s+(\d{1,4})(?![\d.])\b[^\n]*")
ROW = re.compile(r"(?m)^\s*(\d{1,4})[ \t]*(?:[-–|][ \t]*)?(?:\n|[ \t]+[A-ZÀ-Ý])")
UNIT = re.compile(r"\b(?:unid(?:ade)?s?\.?|und\.?|p[eç]ças?|kits?)\b\s*\d+",re.I)
RESET = re.compile(r"(?im)^\s*(?:ANEXO\s+[IVX\d]+|LOTE\s+\d+|TERMO DE REFER[EÊ]NCIA)\b")


def markers(text):
    found=[(m.start(),m.end(),str(int(m.group(1))),'explicit') for m in EXPLICIT.finditer(text)]
    for m in ROW.finditer(text):
        # Só interpreta número isolado como linha se houver unidade próxima.
        if UNIT.search(text[m.end():m.end()+900]) and not any(abs(m.start()-a)<10 for a,_,_,_ in found):
            found.append((m.start(),m.end(),str(int(m.group(1))),'table_row'))
    return sorted(found)


def index_items(pages,max_pages=3):
    """pages: {(document_sequence,page): texto}; cada ocorrência é independente."""
    result=[];active=None;previous=None
    for (sequence,page),text in sorted(pages.items()):
        if previous!=(sequence,page-1):active=None
        points=markers(text)
        resets=[m.start() for m in RESET.finditer(text)]
        boundaries=sorted([(a,b,item,kind) for a,b,item,kind in points]+[(a,a,None,'reset') for a in resets])
        cursor=0
        if active and page-active['header_page']>=max_pages:active=None
        for start,end,item,kind in boundaries:
            if active and start>cursor:active['spans'].append((page,cursor,start))
            if item is None:active=None;cursor=start;continue
            active={'sequence':sequence,'item':item,'header_page':page,'header_start':start,
                    'header_end':end,'recognition':kind,'spans':[]}
            result.append(active);cursor=start
        if active and cursor<len(text):active['spans'].append((page,cursor,len(text)))
        previous=(sequence,page)
    return result


def diverse(documents,limit=5):
    """Descarta sobreposição >=60% do menor intervalo na mesma página/fonte."""
    selected=[]
    for doc in documents:
        m=doc.metadata
        duplicate=False
        for old in selected:
            n=old.metadata
            if m.get('item_number') and (m['pncp_id'],m['document_sequence'],m['item_number'])==(n['pncp_id'],n['document_sequence'],n.get('item_number')) and ' '.join(doc.page_content.split())==' '.join(old.page_content.split()):
                duplicate=True;break
            if (m['pncp_id'],m['document_sequence'],m['page'])!=(n['pncp_id'],n['document_sequence'],n['page']):continue
            overlap=max(0,min(m['end'],n['end'])-max(m['start'],n['start']))
            if overlap/max(1,min(m['end']-m['start'],n['end']-n['start']))>=.6:duplicate=True;break
        if not duplicate:selected.append(doc)
        if len(selected)>=limit:break
    return selected


def select_items(query,pages,rows,fallback,limit=5):
    requested={str(int(m)) for m in re.findall(r'\bitem\s+(\d{1,4})(?![\d.])\b',query,re.I)}
    if not requested:return diverse(fallback,limit)
    words=set(re.findall(r'\w{3,}',fold(query)))
    candidates=[]
    for occurrence in index_items(pages):
        if occurrence['item'] not in requested:continue
        sequence=occurrence['sequence']
        for row in rows:
            ident,text,pncp,seq,page,start,end,url=row
            if seq!=sequence:continue
            for span_page,left,right in occurrence['spans']:
                if page!=span_page or end<=left or start>=right:continue
                page_text=pages[(seq,page)]
                if page_text[start:end]!=text:raise ValueError('Trecho diverge da pagina original')
                a=max(left,start-350);b=min(right,end+650,a+2000)
                if b<=a:continue
                header=page==occurrence['header_page'] and start<=occurrence['header_end'] and end>occurrence['header_start']
                content=page_text[a:b]
                score=len(words & set(re.findall(r'\w{3,}',fold(content))))
                passage_id=hashlib.sha256(f'{ident}:{a}:{b}:{occurrence["item"]}'.encode()).hexdigest()
                metadata={'id':passage_id,'source_chunk_id':ident,'pncp_id':pncp,'document_sequence':seq,'page':page,'start':a,'end':b,
                          'url':url,'score':score,'anchor_start':start,'anchor_end':end,'context_profile':'item_structure',
                          'item_number':occurrence['item'],'item_header_page':occurrence['header_page'],
                          'item_header_start':occurrence['header_start'],'item_recognition':occurrence['recognition'],
                          'item_continuation':'inferred_requires_review' if page!=occurrence['header_page'] else 'header_page'}
                metadata['quantity_candidates']=[{'quote':m.group(0),'start':a+m.start(),'end':a+m.end()} for m in UNIT.finditer(content)]
                candidates.append((header,score,Document(page_content=content,metadata=metadata)))
    # Identidade primeiro; demais fontes por coincidência com pergunta, sem misturar itens.
    candidates.sort(key=lambda x:(-int(x[0]),-x[1],x[2].metadata['document_sequence'],x[2].metadata['page'],x[2].metadata['start']))
    if not candidates:return diverse(fallback,limit)
    return diverse([d for _,_,d in candidates],limit)


def structured_documents(query,snapshot,edital,fallback,filters=None):
    filters=filters or {}
    if 'clause' in filters:return diverse(fallback)
    with connect() as conn:
        conn.execute('SET TRANSACTION READ ONLY')
        params=[snapshot,edital];where='snapshot_id=%s AND pncp_id=%s'
        for key in ('document_sequence','page'):
            if key in filters:where+=' AND '+key+'=%s';params.append(filters[key])
        records=conn.execute('SELECT document_sequence,page,text FROM radar.pages WHERE '+where+' ORDER BY document_sequence,page',params).fetchall()
        # Limite explícito de leitura; falha em vez de truncar identidade silenciosamente.
        if sum(len(t) for _,_,t in records)>8000000:raise ValueError('Escopo excede limite de estrutura')
        pages={(seq,page):text for seq,page,text in records}
        scope=' WHERE c.snapshot_id=%s AND c.pncp_id=%s'
        for key in ('document_sequence','page'):
            if key in filters:scope+=' AND c.'+key+'=%s'
        rows=conn.execute("SELECT c.id,c.text,c.pncp_id,c.document_sequence,c.page,c.start_offset,c.end_offset,d.source->>'url' FROM radar.chunks c JOIN radar.documents d ON d.snapshot_id=c.snapshot_id AND d.pncp_id=c.pncp_id AND d.sequence=c.document_sequence"+scope+' ORDER BY c.document_sequence,c.page,c.start_offset',params).fetchall()
    return select_items(query,pages,rows,fallback)
