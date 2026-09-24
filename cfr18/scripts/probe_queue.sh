#!/bin/sh
set -eu
curl -fsS http://localhost:8098/health >/dev/null
printf '%s\n' "{\"ts\":\"$(date -u +%FT%TZ)\",\"health\":\"ok\"}" >> evidence/probe_results.jsonl
python3 -m ci.evidence_vault append probe --data '{"health":"ok"}'
