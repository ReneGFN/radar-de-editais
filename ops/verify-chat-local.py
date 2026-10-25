"""Banco e recuperação reais; provedor simulado, nunca lê chave nem chama Groq."""
import json
import argparse
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
from radar.chat_api import create_app
from radar.storage import connect

root=Path(__file__).resolve().parents[1]
case=json.loads((root/'datasets/evaluation/pilot-candidate-v1.json').read_text(encoding='utf-8'))['cases'][0]
calls=[]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--serve-ui-qa',action='store_true',help='Servidor temporário de QA, com respostas explicitamente simuladas')
args=parser.parse_args()


class FakeGroq:
    def __init__(self,**kwargs):
        assert kwargs['api_key']=='mock-no-key'

    def with_structured_output(self,*args,**kwargs):
        return self

    def invoke(self,messages):
        payload=json.loads(messages[1].content)
        source=payload['documents'][0]
        calls.append(1)
        return {'parsed':{'status':'answered','reason':'','claims':[{
            'text':'SIMULAÇÃO: resposta para verificar a interface, sem avaliação factual.',
            'evidence':[{'chunk_id':source['chunk_id']}]}]},
            'parsing_error':None,'raw':SimpleNamespace(usage_metadata={})}


with patch('langchain_groq.ChatGroq',FakeGroq),patch('radar.generation.key',return_value='mock-no-key'):
    with TestClient(create_app(free_plan_confirmed=True),base_url='http://127.0.0.1:8766') as client:
        response=client.post('/chat/ask',json={'question':case['question'],'pncp_id':case['pncp_id']},
                             headers={'x-radar-chat':'1'})
        assert response.status_code==200, 'Falha da API local'
        result=response.json()
        assert result['status']=='answered' and len(calls)==1
        assert result['sources'] and result['claims'][0]['source_indices']==[1]
        with connect() as conn:
            conn.execute('SET TRANSACTION READ ONLY')
            for source in result['sources']:
                page=conn.execute('''SELECT text FROM radar.pages WHERE snapshot_id=%s AND pncp_id=%s
                  AND document_sequence=%s AND page=%s''',(result['snapshot_id'],source['pncp_id'],
                  source['document_sequence'],source['page'])).fetchone()
                assert page and source['quote'] in page[0]
        clarification=client.post('/chat/ask',json={'question':'Qual prazo de entrega?'},
                                  headers={'x-radar-chat':'1'})
        assert clarification.status_code==200 and clarification.json()['status']=='needs_clarification'
        assert len(calls)==1
    if args.serve_ui_qa:
        import uvicorn
        print('QA TEMPORÁRIO: PROVEDOR SIMULADO; NENHUMA CHAMADA GROQ REAL.',flush=True)
        uvicorn.run(create_app(free_plan_confirmed=True),host='127.0.0.1',port=8766,
                    proxy_headers=False,server_header=False,access_log=False,log_level='critical')
report={'snapshot_id':result['snapshot_id'],'real_database':True,'retrieval_real':True,
        'provider':'simulated','real_groq_calls':0,'holdout_used':False,
        'api_answer_status':result['status'],'source_page_and_quote_verified':True,
        'clarification_without_generation':True,'factual_accuracy_measured':False}
(root/'reports/chat-local-integration.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report))
