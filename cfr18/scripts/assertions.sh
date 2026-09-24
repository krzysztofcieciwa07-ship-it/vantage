#!/bin/sh
set -eu
test -f evidence/incident.json
test -f evidence/probe_results.jsonl
test -f evidence/self_report.json
python3 -m ci.evidence_vault verify
echo "ASSERTIONS PASS"
