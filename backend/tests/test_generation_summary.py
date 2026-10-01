import importlib.util
import json
from pathlib import Path

spec=importlib.util.spec_from_file_location('generation_summary',Path(__file__).resolve().parents[2]/'ops/summarize-generation.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_public_summary_excludes_answers_and_does_not_score_correctness():
    checkpoint={'model':'model','snapshot_id':'snapshot','reference_sha256':'digest',
        'answers':[{'case_id':'case-1','kind':'answerable','expected_answer':'PRIVATE_EXPECTED',
        'total_latency_ms':100,'response':{'status':'answered','answer':'PRIVATE_ANSWER',
        'citations':[{'quote':'PRIVATE_QUOTE'}],'generation_calls':1,
        'usage':{'input_tokens':10,'output_tokens':20},'generation_latency_ms':90,
        'citation_integrity':'passed'}}],
        'errors':[{'case_id':'case-2','cause_type':'ValueError: Citação inventada'}]}
    report=module.summarize(checkpoint)
    assert report['completed']==1 and report['tested_cases']==2
    assert report['rejected_case_ids']==['case-2']
    assert report['correctness']=='not_scored_pending_human_review'
    assert 'PRIVATE_' not in json.dumps(report)
    assert report['input_tokens_successful_cases']==10
