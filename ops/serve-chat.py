"""Inicia chat em loopback fixo, separado da API de métricas."""
import argparse

import uvicorn
from radar.chat_api import create_app


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--free-plan-confirmed',action='store_true')
    parser.add_argument('--reranking',action='store_true',help='Experimento local coverage_v1; não altera a variante padrão dos relatórios')
    args = parser.parse_args()
    uvicorn.run(create_app(free_plan_confirmed=args.free_plan_confirmed,rerank_profile="coverage_v1" if args.reranking else "none"),host='127.0.0.1',port=8766,
                proxy_headers=False,server_header=False,access_log=False,log_level='critical')
