import json
from datetime import datetime, timezone
from pathlib import Path
from .evidence_vault import verify_chain
ROOT=Path(__file__).resolve().parents[1]
EV=ROOT/"evidence"

def read_jsonl(path):
    if not path.exists(): return []
    out=[]
    for line in path.read_text().splitlines():
        if line.strip(): out.append(json.loads(line))
    return out

def score():
    ok,root,n=verify_chain()
    if not ok:
        raise SystemExit("SCORE VOID: evidence chain tampered")
    required=["incident.json","manifest.json","probe_results.jsonl","self_report.json"]
    missing=[x for x in required if not (EV/x).exists()]
    if missing:
        raise SystemExit("SCORE BLOCKED: missing evidence: "+", ".join(missing))

    probes=read_jsonl(EV/"probe_results.jsonl")
    processed=read_jsonl(ROOT/"data/processed.jsonl")
    events=read_jsonl(ROOT/"data/events.jsonl")
    if not probes:
        raise SystemExit("SCORE BLOCKED: no runtime probes")

    ok_probes=sum(1 for p in probes if p.get("status")=="ok")
    availability=ok_probes/len(probes)
    ids=[p.get("id") for p in processed]
    unique_ids=set(ids)
    duplicates=max(0,len(ids)-len(unique_ids))
    expected=set(range(1,9))
    recovered=len(unique_ids & expected)/len(expected)
    crash_events=sum(1 for e in events if e.get("event")=="crash")
    score=(0.40*availability)+(0.30*recovered)+(0.20*(1.0-min(duplicates/8,1.0)))+(0.10*(1.0 if crash_events else 0.0))

    result={
        "schema":"CFR-18/forensic-score-v1",
        "status":"PASS" if score>=0.90 else "FAIL",
        "score":round(score,4),
        "metrics":{
            "availability":round(availability,4),
            "recovered_job_fraction":round(recovered,4),
            "duplicate_records":duplicates,
            "crash_events":crash_events,
            "probe_samples":len(probes),
        },
        "evidence_entries":n,
        "chain_root":root,
        "generated_at":datetime.now(timezone.utc).isoformat(),
    }
    (EV/"score_result.json").write_text(json.dumps(result,indent=2)+"\n")
    return result

if __name__=="__main__": print(json.dumps(score(),indent=2))
