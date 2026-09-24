#!/bin/sh
set -eu
rm -rf data/* evidence/.chain.jsonl
mkdir -p data evidence
python3 -m ci.evidence_vault append session_start --data '{"seed":"ci-live"}'
docker compose down -v --remove-orphans >/dev/null 2>&1 || true
docker compose up -d --build
trap 'docker compose down -v --remove-orphans' EXIT
until curl -fsS http://localhost:8098/health >/dev/null; do sleep 1; done
for i in $(seq 1 8); do curl -fsS -X POST http://localhost:8098/enqueue -H 'content-type: application/json' -d "{\"id\":$i}" >/dev/null; done
sleep 2
test -s data/events.jsonl
test -s data/processed.jsonl
python3 -m ci.evidence_vault append runtime --data '{"health":"ok","jobs":8}'
cp evidence/.chain.jsonl evidence/.chain.bak
python3 - <<'PY'
from pathlib import Path
p=Path("evidence/.chain.jsonl"); s=p.read_text(); p.write_text(s.replace('"event":"runtime"','"event":"TAMPERED"',1))
PY
if python3 -m ci.evidence_vault verify >/dev/null 2>&1; then echo "TAMPER_DETECTION_FAIL"; exit 1; fi
mv evidence/.chain.bak evidence/.chain.jsonl
python3 -m ci.evidence_vault verify
docker compose ps
echo LIVE_FORENSIC_PASS
