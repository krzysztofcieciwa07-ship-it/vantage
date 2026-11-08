#!/bin/sh
set -eu

DURATION=$(printenv DURATION 2>/dev/null || true)
case "$DURATION" in
  ''|*[!0-9]*)
    echo "BLOCK: DURATION must be set to the incident's positive integer window" >&2
    exit 2
    ;;
esac
if [ "$DURATION" -lt 1 ]; then
  echo "BLOCK: DURATION must be greater than zero" >&2
  exit 2
fi

: > evidence/probe_results.jsonl
START_EPOCH=$(date +%s)
while :; do
  ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  if curl -fsS http://localhost:8098/health >/dev/null 2>&1; then
    printf '%s\n' "{\"ts\":\"$ts\",\"status\":\"ok\"}" >> evidence/probe_results.jsonl
  else
    printf '%s\n' "{\"ts\":\"$ts\",\"status\":\"fail\"}" >> evidence/probe_results.jsonl
  fi

  elapsed=$(($(date +%s) - START_EPOCH))
  if [ "$elapsed" -ge "$DURATION" ]; then
    break
  fi
  sleep 1
done
