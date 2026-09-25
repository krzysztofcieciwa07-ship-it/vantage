import argparse,hashlib,json
from pathlib import Path
from .adaptive_window import required_window
from .evidence_vault import append
ROOT=Path(__file__).resolve().parents[1]
def mutation(seed:int):
    h=int(hashlib.sha256(f"CFR18:{seed}".encode()).hexdigest()[:16],16)
    return {"seed":seed,"variant":("double_process","double_process","silent_loss","reactivation")[h%4],"kill_delay_ms":250+h%1750,"queue_depth":25+h%76}
def main():
    p=argparse.ArgumentParser(); p.add_argument("--seed",type=int,required=True); a=p.parse_args()
    m=mutation(a.seed); now=__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
    incident={"schema":"CFR-18/1","ticket_id":f"CFR18-{a.seed:08d}","opened_at":now,"seed":a.seed,"mutation":m,"hidden_required_window_s":required_window(a.seed),"required_evidence":["incident.json","manifest.json","probe_results.jsonl","self_report.json","bash_history.txt"]}
    ev=ROOT/"evidence"; ev.mkdir(exist_ok=True)
    (ev/"incident.json").write_text(json.dumps(incident,indent=2)+"\n")
    manifest={"schema":"CFR-18/evidence-manifest-v1","session_seed":a.seed,"incident_sha256":hashlib.sha256((ev/"incident.json").read_bytes()).hexdigest(),"created_at":now}
    (ev/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    append("incident_created",{"ticket_id":incident["ticket_id"],"seed":a.seed,"variant":m["variant"]})
    print(json.dumps(incident,indent=2))
if __name__=="__main__": main()
