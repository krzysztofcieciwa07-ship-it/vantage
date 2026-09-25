#!/bin/sh
set -eu
cp evidence/.chain.jsonl evidence/.chain.jsonl.bak
python3 - <<'PY'
from pathlib import Path
p=Path("evidence/.chain.jsonl")
s=p.read_text()
p.write_text(s.replace('"event":"','"event":"TAMPERED-',1))
PY
if python3 -m ci.evidence_vault verify; then
  echo "TAMPER TEST FAIL: chain remained valid"
  exit 1
fi
mv evidence/.chain.jsonl.bak evidence/.chain.jsonl
echo "TAMPER TEST PASS"
