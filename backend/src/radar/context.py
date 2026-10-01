"""Amplia um trecho dentro da página original; não reconstrói nem interpreta tabelas."""
from langchain_core.documents import Document
from .storage import connect


def page_window(document, page, before=350, after=650, max_chars=2000):
    meta=document.metadata
    start,end=meta['start'],meta['end']
    if not isinstance(page,str) or not 0<=start<end<=len(page) or page[start:end]!=document.page_content:
        raise ValueError('Trecho diverge da página original')
    if end-start>max_chars:raise ValueError('Trecho excede limite de contexto')
    padding_before=min(before,max_chars-(end-start))
    left=max(0,start-padding_before)
    right=min(len(page),end+after,left+max_chars)
    metadata=dict(meta,anchor_start=start,anchor_end=end,start=left,end=right,context_profile='page_window')
    return Document(page_content=page[left:right],metadata=metadata)


def expand_documents(documents,snapshot):
    result=[];pages={}
    with connect() as conn:
        conn.execute('SET TRANSACTION READ ONLY')
        for doc in documents:
            m=doc.metadata;key=(m['pncp_id'],m['document_sequence'],m['page'])
            if key not in pages:
                row=conn.execute('SELECT text FROM radar.pages WHERE snapshot_id=%s AND pncp_id=%s AND document_sequence=%s AND page=%s',(snapshot,*key)).fetchone()
                if not row:raise ValueError('Página de contexto ausente')
                pages[key]=row[0]
            result.append(page_window(doc,pages[key]))
    return result
