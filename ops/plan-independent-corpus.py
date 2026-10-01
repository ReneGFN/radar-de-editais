"""Lista candidata de editais novos por região; não baixa PDFs ou altera banco."""
import argparse
import json
from pathlib import Path
from datetime import datetime,timezone
import httpx
from radar.config import emit_json
from radar.ingestion import API,FILES,get,safe_url
from radar.sector import classify_sector

REGIONS={'SP':'Sudeste','RJ':'Sudeste','PR':'Sul','SC':'Sul','BA':'Nordeste','CE':'Nordeste','GO':'Centro-Oeste','DF':'Centro-Oeste','PA':'Norte','AM':'Norte'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('existing')
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    with open(args.existing,encoding='utf-8') as file:existing=json.load(file)
    seen={e['pncp_id'] for e in existing['editais']};candidates=[];errors=[];rate_limited=False
    if args.report.exists():
        previous=json.loads(args.report.read_text(encoding='utf-8'))
        if previous.get('existing_snapshot')==existing['snapshot_id'] and previous.get('search_window')==['20260921','20261001']:
            candidates=previous.get('candidates',[]);errors=previous.get('errors',[])
            if any(c['pncp_id'] in seen for c in candidates):raise ValueError('Candidato sobrepoe corpus antigo')
            seen.update(c['pncp_id'] for c in candidates)
    with httpx.Client(timeout=httpx.Timeout(45,connect=15),follow_redirects=False,headers={'User-Agent':'RadarDeEditais/0.1 (portfolio research)'}) as client:
        for uf,region in REGIONS.items():
            selected=next((c for c in candidates if c['uf']==uf),None)
            if selected:continue
            for page in range(1,6):
                response={}
                try:
                    response=get(client,API,params={'dataInicial':'20260921','dataFinal':'20261001','codigoModalidadeContratacao':6,'uf':uf,'pagina':page,'tamanhoPagina':50})
                    for item in response.get('data',[]):
                        identifier=item.get('numeroControlePNCP')
                        if not identifier or identifier in seen or classify_sector(item.get('objetoCompra',''))!='in_scope_candidate':continue
                        cnpj=item['orgaoEntidade']['cnpj'];year=item['anoCompra'];sequence=item['sequencialCompra']
                        try:
                            files=get(client,FILES.format(cnpj=cnpj,year=year,sequence=sequence))
                        except (httpx.HTTPError,ValueError,KeyError) as exc:
                            errors.append({'uf':uf,'page':page,'pncp_id':identifier,'stage':'file_listing','error_type':type(exc).__name__,'http_status':getattr(getattr(exc,'response',None),'status_code',None)})
                            if getattr(getattr(exc,'response',None),'status_code',None)==429:
                                rate_limited=True;break
                            continue
                        allowed=[f for f in files if f.get('tipoDocumentoId')==2] if isinstance(files,list) else []
                        if not allowed:continue
                        selected={'pncp_id':identifier,'uf':uf,'region':region,'agency':item['orgaoEntidade']['razaoSocial'],'sector_triage':'in_scope_candidate','official_url':f'https://pncp.gov.br/app/editais/{cnpj}/{year}/{sequence}','documents':[{'sequence':f['sequencialDocumento'],'url':safe_url(f['url']),'type_id':2,'sha256_status':'pending_download'} for f in allowed]}
                        seen.add(identifier);break
                except (httpx.HTTPError,ValueError,KeyError,TypeError) as exc:
                    errors.append({'uf':uf,'page':page,'stage':'publication_query','error_type':type(exc).__name__,'http_status':getattr(getattr(exc,'response',None),'status_code',None)})
                    if getattr(getattr(exc,'response',None),'status_code',None)==429:rate_limited=True
                if rate_limited or selected or (response and page>=response.get('totalPaginas',0)):break
            if selected:candidates.append(selected)
            emit_json(args.report,{'state':'collection_in_progress_metadata_only','existing_snapshot':existing['snapshot_id'],'candidates':candidates,'errors':errors,'target':10,'complete':False,'search_window':['20260921','20261001']})
            print(json.dumps({'uf':uf,'candidate_selected':bool(selected),'total':len(candidates)}),flush=True)
            if rate_limited:break
    report={'captured_at_utc':datetime.now(timezone.utc).isoformat(),'rate_limited':rate_limited,'state':'metadata_candidates_not_downloaded_or_indexed','existing_snapshot':existing['snapshot_id'],'candidates':candidates,'errors':errors,'search_window':['20260921','20261001'],'target':10,'complete':len(candidates)==10,'edital_overlap':0,'pdf_hash_overlap_check':'pending_download','questions':'not_prepared_not_executed','representative':False,'production_promotion':False}
    emit_json(args.report,report)


if __name__=='__main__':main()
