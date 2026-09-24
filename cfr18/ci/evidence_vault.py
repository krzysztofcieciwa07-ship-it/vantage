#!/usr/bin/env python3
import argparse,hashlib,json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; VAULT=ROOT/"evidence"; CHAIN=VAULT/".chain.jsonl"
GENESIS=hashlib.sha256(b"CFR-18-GENESIS").hexdigest()
def canon(x): return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def verify_chain(path=CHAIN):
    if not path.exists(): return True,GENESIS,0
    prev=GENESIS; count=0
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            if not raw.strip(): continue
            e=json.loads(raw); claimed=e.get("hash"); body=dict(e); body.pop("hash",None)
            expected=hashlib.sha256(bytes.fromhex(prev)+canon(body)).hexdigest()
            if claimed!=expected or e.get("prev_hash")!=prev: return False,prev,count
            prev=claimed; count+=1
    except (OSError,ValueError,json.JSONDecodeError): return False,prev,count
    return True,prev,count
def append(event,data=None,path=CHAIN):
    ok,last,_=verify_chain(path)
    if path.exists() and not ok: raise RuntimeError("evidence chain invalid; refusing to append")
    path.parent.mkdir(parents=True,exist_ok=True)
    body={"ts":datetime.now(timezone.utc).isoformat(),"event":event,"data":data or {},"prev_hash":last}
    body["hash"]=hashlib.sha256(bytes.fromhex(last)+canon(body)).hexdigest()
    with path.open("a",encoding="utf-8") as f: f.write(json.dumps(body,sort_keys=True,separators=(",",":"))+"\n")
    return body["hash"]
def main():
    p=argparse.ArgumentParser(); s=p.add_subparsers(dest="cmd",required=True)
    a=s.add_parser("append"); a.add_argument("event"); a.add_argument("--data",default="{}"); s.add_parser("verify")
    x=p.parse_args()
    if x.cmd=="append":
        try: print(append(x.event,json.loads(x.data))); return 0
        except Exception as e: print(f"ERROR: {e}",file=sys.stderr); return 2
    ok,last,n=verify_chain(); print(json.dumps({"valid":ok,"entries":n,"root":last},indent=2)); return 0 if ok else 2
if __name__=="__main__": raise SystemExit(main())
