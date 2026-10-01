"""Executa uma pergunta no GPT-OSS 120B e salva a resposta só no diretório privado."""
import argparse
import json
from datetime import datetime,timezone
from radar.config import private_root,emit_json
from radar.generation import answer

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('question')
parser.add_argument('--snapshot',required=True)
parser.add_argument('--edital',required=True)
parser.add_argument('--confirm-free-plan',action='store_true')
args=parser.parse_args()
try:
    result=answer(args.question,args.snapshot,args.edital,free_plan_confirmed=args.confirm_free_plan)
except Exception as exc:
    print(json.dumps({'status':'failed','error_type':type(exc).__name__}))
    raise SystemExit(1) from None
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
path=private_root()/'generation'/f'{stamp}.json'
emit_json(path,result)
print(json.dumps({'status':result['status'],'generation_calls':result['generation_calls'],'private_output':str(path)},ensure_ascii=False))
