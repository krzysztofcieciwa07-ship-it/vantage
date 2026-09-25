import json,re
from datetime import datetime,timezone
from pathlib import Path
from .evidence_vault import verify_chain,verify_bound_files
ROOT=Path(__file__).resolve().parents[1]; EV=ROOT/"evidence"
def read_jsonl(p): return [json.loads(x) for x in p.read_text().splitlines() if x.strip()] if p.exists() else []
def investigation_quality():
    p=EV/"bash_history.txt"
    if not p.exists(): return 0.0
    t=p.read_text().lower()
    sig={r"docker\s+(compose\s+)?logs":.20,r"curl.*health":.15,r"grep.*processing":.15,r"processed\.jsonl":.15,r"events\.jsonl":.10,r"docker\s+compose\s+(stop|restart)":.10,r"git\s+diff":.10,r"probe":.05}
    return min(1.0,sum(w for pat,w in sig.items() if re.search(pat,t)))
def score():
    chain=verify_chain()
    if not chain["valid"]: raise SystemExit("SCORE VOID: evidence chain tampered")
    bound,reason=verify_bound_files()
    if not bound: raise SystemExit("SCORE VOID: "+reason)
    probes=read_jsonl(EV/"probe_results.jsonl"); processed=read_jsonl(ROOT/"data/processed.jsonl"); events=read_jsonl(ROOT/"data/events.jsonl")
    incident=json.loads((EV/"incident.json").read_text()); report=json.loads((EV/"self_report.json").read_text())
    if not probes: raise SystemExit("SCORE BLOCKED: no runtime probes")
    availability=sum(p.get("status")=="ok" for p in probes)/len(probes)
    ids=[x.get("id") for x in processed]; unique=set(ids); duplicates=max(0,len(ids)-len(unique))
    recovered=len(unique & set(range(1,9)))/8; crashes=sum(e.get("event")=="crash" for e in events); inv=investigation_quality()
    correct=report.get("fault_type")==incident["mutation"]["variant"]
    base=.20*availability+.25*recovered+.20*(1-min(duplicates/8,1))+.10*(1 if crashes else 0)+.05*inv
    total=max(0,min(1,base+.20*(.15 if correct else -.05)))
    result={"schema":"CFR-18/forensic-score-v2","status":"PASS" if total>=.90 else "FAIL","score":round(total,4),"metrics":{"availability":round(availability,4),"recovered_job_fraction":round(recovered,4),"duplicate_records":duplicates,"crash_events":crashes,"probe_samples":len(probes),"investigation_quality":round(inv,4),"self_report_correct":correct},"chain_root_before_score":chain["root"],"generated_at":datetime.now(timezone.utc).isoformat()}
    (EV/"score_result.json").write_text(json.dumps(result,indent=2)+"\n"); return result
if __name__=="__main__": print(json.dumps(score(),indent=2))
