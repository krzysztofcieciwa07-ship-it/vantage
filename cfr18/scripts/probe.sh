#!/bin/sh
set -eu
DURATION=$(printenv DURATION 2>/dev/null || true)
if [ -z "$DURATION" ]; then DURATION=120; fi
: > evidence/probe_results.jsonl
i=0
while [ "$i" -lt "$DURATION" ]; do
  ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  if curl -fsS http://localhost:8098/health >/dev/null 2>&1; then printf '%s\n' "{\"ts\":\"$ts\",\"status\":\"ok\"}" >> evidence/probe_results.jsonl; else printf '%s\n' "{\"ts\":\"$ts\",\"status\":\"fail\"}" >> evidence/probe_results.jsonl; fi
  i=$((i+1)); sleep 1
done
