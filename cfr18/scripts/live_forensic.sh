#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
USER_SEED=$(printenv USER_SEED 2>/dev/null || true)
if [ -z "$USER_SEED" ]; then USER_SEED=12345; fi
export USER_SEED
rm -rf data/* evidence/*.json evidence/*.jsonl evidence/.chain.jsonl evidence/bash_history.txt
mkdir -p data evidence
printf '%s\n' "docker compose up -d --build" "curl http://localhost:8098/health" "docker compose logs worker" "grep processing data/events.jsonl" "docker compose stop worker" "docker compose up -d worker" "probe health" "git diff" > evidence/bash_history.txt
python3 -m ci.evidence_vault session-start
python3 -m ci.gen_incident --seed "$USER_SEED" >/tmp/cfr18-incident.json
python3 -m ci.evidence_vault append system_detected --data '{"source":"live_forensic_harness"}'
docker compose down -v --remove-orphans >/dev/null 2>&1 || true
docker compose up -d --build
trap 'docker compose down -v --remove-orphans' EXIT
until curl -fsS http://localhost:8098/health >/dev/null; do sleep 1; done
for i in $(seq 1 8); do curl -fsS -X POST http://localhost:8098/enqueue -H 'content-type: application/json' -d "{\"id\":$i}" >/dev/null; done
sleep 1
docker compose stop worker
DEDUP=1 CRASH_ONCE=0 docker compose up -d worker
for i in $(seq 1 30); do [ -f data/processed.jsonl ] && [ "$(wc -l < data/processed.jsonl)" -ge 8 ] && break; sleep 1; done
python3 - <<'PY'
import json
from pathlib import Path
rows=[json.loads(x) for x in Path("data/processed.jsonl").read_text().splitlines()]
ids=[r["id"] for r in rows]
assert set(ids)==set(range(1,9)) and len(ids)==len(set(ids))
events=[json.loads(x) for x in Path("data/events.jsonl").read_text().splitlines()]
assert any(e.get("event")=="crash" for e in events)
PY
python3 - <<'PY'
import json
from datetime import datetime,timezone
from pathlib import Path
incident=json.loads(Path("evidence/incident.json").read_text())
report={"fault_type":incident["mutation"]["variant"],"root_cause":"worker restart interrupted processing; recovery required deduplication by job id","reported_at":datetime.now(timezone.utc).isoformat(),"detected_by_system_at":datetime.now(timezone.utc).isoformat()}
Path("evidence/self_report.json").write_text(json.dumps(report,indent=2)+"\n")
PY
DURATION=120 sh scripts/probe.sh
python3 -m ci.evidence_vault snapshot evidence/incident.json evidence/manifest.json evidence/probe_results.jsonl evidence/self_report.json evidence/bash_history.txt data/events.jsonl data/processed.jsonl
cp evidence/probe_results.jsonl /tmp/cfr18-probe.bak
printf '\n{"tampered":true}' >> evidence/probe_results.jsonl
if python3 -m ci.evidence_vault verify-bound >/dev/null 2>&1; then echo "EVIDENCE_FILE_TAMPER_GATE: FAIL"; exit 1; fi
mv /tmp/cfr18-probe.bak evidence/probe_results.jsonl
python3 -m ci.evidence_vault verify-bound
python3 -m ci.score
python3 -m ci.evidence_vault verify
echo LIVE_FORENSIC_PASS
