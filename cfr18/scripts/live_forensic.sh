#!/bin/sh
set -eu
rm -rf data/* evidence/.chain.jsonl evidence/probe_results.jsonl evidence/score_result.json
a=0
mkdir -p data evidence
python3 -m ci.evidence_vault append session_start --data '{"seed":"ci-live"}'
docker compose down -v --remove-orphans >/dev/null 2>&1 || true
docker compose up -d --build
trap 'docker compose down -v --remove-orphans' EXIT
until curl -fsS http://localhost:8098/health >/dev/null; do sleep 1; done
for i in $(seq 1 8); do curl -fsS -X POST http://localhost:8098/enqueue -H 'content-type: application/json' -d "{\"id\":$i}" >/dev/null; done
sleep 1
docker compose stop worker
DEDUP=1 CRASH_ONCE=0 docker compose up -d worker
for i in $(seq 1 30); do [ -f data/processed.jsonl ] && [ "$(wc -l < data/processed.jsonl)" -ge 8 ] && break; sleep 1; done
test -s data/events.jsonl
test -s data/processed.jsonl
python3 - <<'PY'
import json
from pathlib import Path
rows=[json.loads(x) for x in Path("data/processed.jsonl").read_text().splitlines()]
ids=[r["id"] for r in rows]
assert set(ids)==set(range(1,9)), ids
assert len(ids)==len(set(ids)), ids
PY
python3 -m ci.evidence_vault append runtime_recovered --data '{"health":"ok","jobs":8,"recovery":"dedup","unique_processed":8}'

# Runtime stability evidence: one health probe per second for 120 seconds.
# This is deliberately longer than the 100s minimum adaptive window used by the CI seed.
: > evidence/probe_results.jsonl
n=0
while [ "$n" -lt 120 ]; do
  ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  if curl -fsS http://localhost:8098/health >/dev/null 2>&1; then
    printf '%s\n' "{\"ts\":\"$ts\",\"status\":\"ok\"}" >> evidence/probe_results.jsonl
  else
    printf '%s\n' "{\"ts\":\"$ts\",\"status\":\"fail\"}" >> evidence/probe_results.jsonl
  fi
  n=$((n+1))
  sleep 1
done
python3 -m ci.evidence_vault append stability_window --data '{"samples":120,"interval_seconds":1,"required_minimum_seconds":100}'

# Explicit tamper gate: mutate a chained event, require verification to fail, then restore it.
cp evidence/.chain.jsonl evidence/.chain.bak
python3 - <<'PY'
from pathlib import Path
p=Path("evidence/.chain.jsonl")
s=p.read_text()
p.write_text(s.replace('"event":"runtime_recovered"','"event":"TAMPERED"',1))
PY
if python3 -m ci.evidence_vault verify >/dev/null 2>&1; then
  echo "TAMPER_DETECTION_FAIL"
  exit 1
fi
mv evidence/.chain.bak evidence/.chain.jsonl
python3 -m ci.evidence_vault verify
docker compose ps
echo LIVE_FORENSIC_PASS
