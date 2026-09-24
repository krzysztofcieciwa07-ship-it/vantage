import argparse,hashlib,json
from pathlib import Path
from .adaptive_window import required_window
from .evidence_vault import append
ROOT=Path(__file__).resolve().parents[1]
def mutation(seed:int):
    h=int(hashlib.sha256(f"CFR18:{seed}".encode()).hexdigest()[:16],16)
    return {"seed":seed,"variant":("double_process","double_process","silent_loss","reactivation")[h%4],"kill_delay_ms":250+h%1750,"queue_depth":25+h%76}
def main():
    p=argparse.ArgumentParser(); p.add_argument("--seed",type=int,required=True); a=p.parse_args(); m=mutation(a.seed)
    incident={"schema":"CFR-18/1","seed":a.seed,"mutation":m,"hidden_required_window_s":required_window(a.seed),"required_evidence":["incident.json","manifest.json","probe_results.jsonl","self_report.json"]}
    (ROOT/"evidence").mkdir(exist_ok=True); (ROOT/"evidence/incident.json").write_text(json.dumps(incident,indent=2)+"\n")
    append("incident_created",incident); print(json.dumps(incident,indent=2))
if __name__=="__main__": main()
