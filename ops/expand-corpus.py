"""Amplia a base por cotas geográficas, preservando os dez editais iniciais."""
import argparse
import copy
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from radar.ingestion import select_and_download,matches_sector
from radar.config import PROJECT, emit_json

REGIONS = {"PR":"Sul", "RS":"Sul", "MG":"Sudeste", "RJ":"Sudeste", "SP":"Sudeste",
           "BA":"Nordeste", "PE":"Nordeste", "GO":"Centro-Oeste", "MT":"Centro-Oeste",
           "PA":"Norte", "AM":"Norte"}

def expand(seed, start, end, resume=None):
    original=json.loads(seed.read_text(encoding="utf-8"))
    if len(original["editais"])!=10 or original["uf"]!="SP":
        raise ValueError("Esperado o manifesto inicial de dez editais SP")
    editais=copy.deepcopy(original["editais"])
    for edital in editais:
        edital["uf"]="SP"
    sources=[original["snapshot_id"]]
    seen={e["pncp_id"] for e in editais}
    previous=json.loads(resume.read_text(encoding="utf-8")) if resume else None
    for index,uf in enumerate(REGIONS):
        if uf=="SP": continue
        retained=[e for e in previous["editais"] if e["uf"]==uf] if previous else []
        if len(retained)==2 and all(matches_sector(e["object"]) for e in retained):
            source_index=list(REGIONS).index(uf)+1 if list(REGIONS).index(uf)<list(REGIONS).index("SP") else list(REGIONS).index(uf)
            partial={"editais":retained,"snapshot_id":previous["source_snapshots"][source_index],"selection_complete":True}
        else:
            partial=select_and_download(start,end,2,uf)
        if not partial["selection_complete"]:
            # Fallback documentado: aumenta o intervalo apenas no estado insuficiente.
            partial=select_and_download("20260901",end,2,uf)
        if len(partial["editais"])!=2:
            raise ValueError(f"Cota de {uf} incompleta; manifestos parciais preservados")
        for edital in partial["editais"]:
            if edital["pncp_id"] in seen or edital["uf"]!=uf:
                raise ValueError("Duplicação ou UF divergente")
            seen.add(edital["pncp_id"])
            editais.append(edital)
        sources.append(partial["snapshot_id"])
        print(json.dumps({"uf_completed":uf,"total":len(editais)}),flush=True)
    identity=[{"pncp_id":e["pncp_id"],"documents":e["documents"]} for e in editais]
    snapshot=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()[:16]
    manifest=PROJECT/"datasets/manifests"/f"{snapshot}.json"
    result={"sector":"informatica","uf":"MULTI","captured_at":datetime.now(timezone.utc).isoformat(),
            "snapshot_id":snapshot,"editais":editais,"selection_complete":True,"rejections":[],
            "source_snapshots":sources,"sampling":{"method":"convenience_with_state_quotas",
                "seed_sp":10,"additional_per_state":2,"additional_window":[start,end],
                "fallback_start":"20260901","representative":False}}
    if not manifest.exists(): emit_json(manifest,result)
    report={"snapshot_id":snapshot,"editais":len(editais),"states":dict(Counter(e["uf"] for e in editais)),
            "regions":dict(Counter(REGIONS[e["uf"]] for e in editais)),"unique_pncp_ids":len(seen),
            "documents":sum(len(e["documents"]) for e in editais),"source_snapshots":sources,
            "sampling":result["sampling"],"manifest":str(manifest.relative_to(PROJECT))}
    emit_json(PROJECT/"reports/amostra-30.json",report)
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return manifest

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("seed",type=Path)
    parser.add_argument("--start",default="20260921")
    parser.add_argument("--end",default="20261001")
    parser.add_argument("--resume",type=Path)
    args=parser.parse_args()
    expand(args.seed,args.start,args.end,args.resume)
