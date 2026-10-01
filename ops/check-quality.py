"""Confere critérios de qualidade localmente; não promove snapshot automaticamente."""
import argparse
import json
from pathlib import Path
from radar.config import emit_json
from radar.quality import assess_release

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('review',type=Path)
parser.add_argument('--report',type=Path,required=True)
args=parser.parse_args()
if args.review.stat().st_size>2*1024*1024:raise ValueError('Revisão excede o limite')
review=json.loads(args.review.read_text(encoding='utf-8'))
if not isinstance(review.get('cases'),list):raise ValueError('Casos ausentes')
result=assess_release(review['cases'])
emit_json(args.report,result)
print(json.dumps({'decision':result['decision'],'reasons':result['reasons']}))
