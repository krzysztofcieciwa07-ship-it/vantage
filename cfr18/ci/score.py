import json
from pathlib import Path
from .evidence_vault import verify_chain
ROOT=Path(__file__).resolve().parents[1]
def score():
    ok,root,n=verify_chain()
    if not ok: raise SystemExit("SCORE VOID: evidence chain tampered")
    required=["incident.json","manifest.json","probe_results.jsonl","self_report.json"]; missing=[x for x in required if not (ROOT/"evidence"/x).exists()]
    if missing: raise SystemExit("SCORE BLOCKED: missing evidence: "+", ".join(missing))
    r={"status":"ELIGIBLE","evidence_entries":n,"chain_root":root,"note":"Numeric scoring waits for live runtime metrics."}
    (ROOT/"evidence/score_result.json").write_text(json.dumps(r,indent=2)+"\n"); return r
if __name__=="__main__": print(json.dumps(score(),indent=2))
