#!/bin/sh
set -eu
for i in $(seq 1 50); do
  curl -fsS -X POST http://localhost:8098/enqueue -H 'content-type: application/json' -d "{\"id\":$i}" >/dev/null
done
python3 -m ci.evidence_vault append load_completed --data '{"jobs":50}'
