#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
python3 -m ci.evidence_vault verify
python3 -m ci.evidence_vault verify-bound
for f in evidence/incident.json evidence/manifest.json evidence/probe_results.jsonl evidence/self_report.json evidence/bash_history.txt data/events.jsonl data/processed.jsonl; do test -s "$f"; done
python3 - <<'PY'
import json
from pathlib import Path
probes=[json.loads(x) for x in Path("evidence/probe_results.jsonl").read_text().splitlines() if x.strip()]
rows=[json.loads(x) for x in Path("data/processed.jsonl").read_text().splitlines() if x.strip()]
events=[json.loads(x) for x in Path("data/events.jsonl").read_text().splitlines() if x.strip()]
assert len(probes)>=100 and all(p.get("status")=="ok" for p in probes)
ids=[x["id"] for x in rows]
assert set(ids)==set(range(1,9)) and len(ids)==len(set(ids))
assert any(e.get("event")=="crash" for e in events)
print("ASSERTIONS_PASS")
PY
