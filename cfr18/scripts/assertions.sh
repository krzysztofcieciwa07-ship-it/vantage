#!/bin/sh
set -eu
test -s data/events.jsonl
test -s data/processed.jsonl
test "$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8098/health)" = "200"
python3 -m ci.evidence_vault verify
echo "ASSERTIONS PASS"
