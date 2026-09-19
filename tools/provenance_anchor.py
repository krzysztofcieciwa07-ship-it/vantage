#!/usr/bin/env python3
import argparse, hashlib, json
from pathlib import Path

def sha256(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def canonical(record): return json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
def build(commit,evidence,replay,previous_hash="0"*64):
    r={"version":1,"commit":commit,"evidence_sha256":sha256(evidence),"replay_sha256":sha256(replay),"previous_hash":previous_hash}
    r["record_hash"]=hashlib.sha256(canonical(r)).hexdigest()
    return r
def verify(path,expected_commit=None):
    r=json.loads(path.read_text())
    for k in ("version","commit","evidence_sha256","replay_sha256","previous_hash","record_hash"):
        if k not in r: raise SystemExit("PROVENANCE_ANCHOR: missing field "+k)
    signed=dict(r); actual=signed.pop("record_hash")
    if actual != hashlib.sha256(canonical(signed)).hexdigest(): raise SystemExit("PROVENANCE_ANCHOR: record_hash mismatch")
    if expected_commit and r["commit"] != expected_commit: raise SystemExit("PROVENANCE_ANCHOR: commit mismatch")
    print("PROVENANCE_ANCHOR: PASS")
    print("record_hash="+actual)
    print("commit="+r["commit"])
def main():
    p=argparse.ArgumentParser(); s=p.add_subparsers(dest="command",required=True)
    b=s.add_parser("build"); b.add_argument("--commit",required=True); b.add_argument("--evidence",type=Path,required=True); b.add_argument("--replay",type=Path,required=True); b.add_argument("--previous-hash",default="0"*64); b.add_argument("--output",type=Path,required=True)
    v=s.add_parser("verify"); v.add_argument("--anchor",type=Path,required=True); v.add_argument("--expected-commit")
    a=p.parse_args()
    if a.command=="build": a.output.write_text(json.dumps(build(a.commit,a.evidence,a.replay,a.previous_hash),sort_keys=True)+"\n"); print("PROVENANCE_ANCHOR: CREATED")
    else: verify(a.anchor,a.expected_commit)
if __name__=="__main__": raise SystemExit(main())
