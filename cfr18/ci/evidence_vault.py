#!/usr/bin/env python3
import argparse,hashlib,json,os
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; VAULT=ROOT/"evidence"; CHAIN=VAULT/".chain.jsonl"
GENESIS=hashlib.sha256(b"CFR-18-GENESIS").hexdigest()
def canon(x): return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def verify_chain(path=CHAIN):
    if not path.exists(): return {"valid":True,"root":GENESIS,"entries":0,"reason":"genesis"}
    prev=GENESIS; n=0
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            if not raw.strip(): continue
            e=json.loads(raw); claimed=e.get("hash"); body=dict(e); body.pop("hash",None)
            expected=hashlib.sha256(bytes.fromhex(prev)+canon(body)).hexdigest()
            if claimed!=expected or e.get("prev_hash")!=prev: return {"valid":False,"root":prev,"entries":n,"reason":f"chain failure at entry {n}"}
            prev=claimed; n+=1
    except Exception as exc: return {"valid":False,"root":prev,"entries":n,"reason":str(exc)}
    return {"valid":True,"root":prev,"entries":n,"reason":"ok"}
def append(event,data=None):
    r=verify_chain()
    if not r["valid"]: raise RuntimeError("evidence chain invalid; refusing to append")
    VAULT.mkdir(parents=True,exist_ok=True)
    body={"ts":datetime.now(timezone.utc).isoformat(),"event":event,"data":data or {},"prev_hash":r["root"]}
    body["hash"]=hashlib.sha256(bytes.fromhex(r["root"])+canon(body)).hexdigest()
    with CHAIN.open("a",encoding="utf-8") as f: f.write(json.dumps(body,sort_keys=True,separators=(",",":"))+"\n")
    return body["hash"]
def file_sha256(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def bind_files(paths):
    files=[]
    for rel in paths:
        p=ROOT/rel
        if not p.exists(): raise FileNotFoundError(rel)
        files.append({"path":rel,"sha256":file_sha256(p),"bytes":p.stat().st_size})
    append("evidence_snapshot",{"files":files}); return files
def verify_bound_files():
    r=verify_chain()
    if not r["valid"]: return False,r["reason"]
    latest=None
    if not CHAIN.exists(): return False,"chain missing"
    for raw in CHAIN.read_text().splitlines():
        if raw.strip():
            e=json.loads(raw)
            if e.get("event")=="evidence_snapshot": latest=e["data"].get("files",[])
    if latest is None: return False,"no evidence_snapshot"
    for item in latest:
        p=ROOT/item["path"]
        if not p.exists(): return False,"bound file missing: "+item["path"]
        if file_sha256(p)!=item["sha256"]: return False,"bound file changed: "+item["path"]
    return True,"ok"
def main():
    p=argparse.ArgumentParser(); s=p.add_subparsers(dest="cmd",required=True)
    a=s.add_parser("append"); a.add_argument("event"); a.add_argument("--data",default="{}")
    b=s.add_parser("snapshot"); b.add_argument("paths",nargs="+")
    s.add_parser("verify"); s.add_parser("verify-bound"); s.add_parser("session-start")
    x=p.parse_args()
    if x.cmd=="append": print(append(x.event,json.loads(x.data))); return 0
    if x.cmd=="snapshot": print(json.dumps(bind_files(x.paths),indent=2)); return 0
    if x.cmd=="session-start": print(append("session_start",{"seed":os.environ.get("USER_SEED","default")})); return 0
    if x.cmd=="verify":
        r=verify_chain(); print(json.dumps(r,indent=2)); return 0 if r["valid"] else 2
    if x.cmd=="verify-bound":
        ok,reason=verify_bound_files(); print(json.dumps({"valid":ok,"reason":reason},indent=2)); return 0 if ok else 2
if __name__=="__main__": raise SystemExit(main())
