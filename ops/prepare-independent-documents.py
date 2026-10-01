"""Baixa PDFs candidatos e extrai páginas privadas; não cria vetores ou altera banco."""
import argparse
import hashlib
import json
from io import BytesIO
from importlib.metadata import version
from pathlib import Path
from datetime import datetime,timezone
import httpx
from pypdf import PdfReader
from radar.config import private_root,emit_json
from radar.ingestion import get


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidates',type=Path)
    parser.add_argument('existing',type=Path)
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    selection=json.loads(args.candidates.read_text(encoding='utf-8'));existing=json.loads(args.existing.read_text(encoding='utf-8'))
    oldids={e['pncp_id'] for e in existing['editais']};oldhashes={d['sha256'] for e in existing['editais'] for d in e['documents']}
    raw=args.candidates.read_bytes();digest=hashlib.sha256(raw).hexdigest();root=private_root();checkpoint=root/'independent'/f'pages-{digest[:16]}.json'
    prepared=json.loads(checkpoint.read_text(encoding='utf-8')) if checkpoint.exists() else {'candidate_sha256':digest,'documents':[],'errors':[]}
    if prepared['candidate_sha256']!=digest:raise ValueError('Checkpoint diverge')
    done={(d['pncp_id'],d['document_sequence']) for d in prepared['documents']};rate_limited=False
    def save():
        emit_json(checkpoint,prepared)
        docs=[{k:d[k] for k in ('pncp_id','uf','region','agency','document_sequence','sha256','url','bytes','page_count','low_text_pages','sha_overlap_existing')} for d in prepared['documents']]
        emit_json(args.report,{'captured_at_utc':datetime.now(timezone.utc).isoformat(),'candidate_sha256':digest,'existing_snapshot':existing['snapshot_id'],'state':'downloaded_extracted_not_indexed','documents':docs,'errors':prepared['errors'],'rate_limited':rate_limited,'extractor':{'package':'pypdf','version':version('pypdf')},'database_changes':0,'groq_calls':0,'reference_questions':'draft_not_executed'})
    with httpx.Client(timeout=httpx.Timeout(45,connect=15),follow_redirects=False,headers={'User-Agent':'RadarDeEditais/0.1 (portfolio research)'}) as client:
        for edital in selection['candidates']:
            if edital['pncp_id'] in oldids:raise ValueError('Edital sobrepõe corpus antigo')
            for doc in edital['documents']:
                if (edital['pncp_id'],doc['sequence']) in done:continue
                try:
                    content=get(client,doc['url'],binary=True)
                    if not content.startswith(b'%PDF-'):raise ValueError('Documento não PDF')
                    sha=hashlib.sha256(content).hexdigest();pdf=root/'raw'/f'{sha}.pdf';pdf.parent.mkdir(parents=True,exist_ok=True)
                    if not pdf.exists():pdf.write_bytes(content)
                    reader=PdfReader(BytesIO(content));pages=[]
                    for index,page in enumerate(reader.pages,1):
                        text=page.extract_text() or ''
                        pages.append({'page':index,'text':text,'quality':'text' if len(text.strip())>=80 else 'needs_review'})
                    prepared['documents'].append({'pncp_id':edital['pncp_id'],'uf':edital['uf'],'region':edital['region'],'agency':edital['agency'],'document_sequence':doc['sequence'],'sha256':sha,'url':doc['url'],'bytes':len(content),'page_count':len(pages),'low_text_pages':sum(p['quality']!='text' for p in pages),'sha_overlap_existing':sha in oldhashes,'pages':pages})
                    done.add((edital['pncp_id'],doc['sequence']))
                    print(json.dumps({'prepared':len(done),'pncp_id':edital['pncp_id'],'sequence':doc['sequence'],'pages':len(pages),'hash_overlap':sha in oldhashes}),flush=True)
                except Exception as exc:
                    status=getattr(getattr(exc,'response',None),'status_code',None)
                    prepared['errors'].append({'pncp_id':edital['pncp_id'],'document_sequence':doc['sequence'],'error_type':type(exc).__name__,'http_status':status})
                    if status==429:rate_limited=True
                    print(json.dumps({'error_type':type(exc).__name__,'http_status':status}),flush=True)
                save()
                if rate_limited:return
    save()


if __name__=='__main__':main()
