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
FIRST_EPOCH=""
while :; do
  sample=$(python3 - <<'PY'
from datetime import datetime, timezone
now = datetime.now(timezone.utc)
print(now.isoformat())
print(f"{now.timestamp():.6f}")
PY
)
  ts=$(printf '%s\n' "$sample" | sed -n '1p')
  epoch=$(printf '%s\n' "$sample" | sed -n '2p')
  if [ -z "$FIRST_EPOCH" ]; then
    FIRST_EPOCH="$epoch"
  fi

  if curl -fsS http://localhost:8098/health >/dev/null 2>&1; then
    status=ok
  else
    status=fail
  fi
  printf '%s\n' "{\"ts\":\"$ts\",\"status\":\"$status\"}" >> evidence/probe_results.jsonl

  elapsed_ok=$(python3 - "$FIRST_EPOCH" "$epoch" "$DURATION" <<'PY'
import sys
start, now, required = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
print("yes" if now - start >= required else "no")
PY
)
  if [ "$elapsed_ok" = "yes" ]; then
    break
  fi
  sleep 1
done
