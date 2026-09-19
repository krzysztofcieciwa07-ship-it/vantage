#!/usr/bin/env python3
import hashlib, os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/"evidence/vantage-verification.txt"
def sha256(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def parse(p):
    out={}
    for line in p.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            k,v=line.split("=",1); out[k]=v
    return out
def main():
    if not EVIDENCE.is_file(): raise SystemExit("INDEPENDENT_VERIFY: evidence file missing")
    v=parse(EVIDENCE)
    for k in ("commit","afe_vantage_sha256","tests_sha256"):
        if k not in v: raise SystemExit("INDEPENDENT_VERIFY: missing field "+k)
    if os.environ.get("GITHUB_SHA") and v["commit"] != os.environ["GITHUB_SHA"]: raise SystemExit("INDEPENDENT_VERIFY: commit mismatch")
    checks={"afe_vantage_sha256":sha256(ROOT/"afe_vantage.py"),"tests_sha256":sha256(ROOT/"tests/test_afe_vantage.py")}
    for k,a in checks.items():
        if v[k] != a: raise SystemExit("INDEPENDENT_VERIFY: "+k+" mismatch")
    print("INDEPENDENT_VERIFY: PASS")
    print("commit="+v["commit"])
    return 0
if __name__=="__main__": raise SystemExit(main())
