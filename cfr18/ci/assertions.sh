#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
python3 -m ci.evidence_vault verify
python3 -m ci.evidence_vault verify-bound
for f in evidence/incident.json evidence/manifest.json evidence/probe_results.jsonl evidence/participant_submission.json data/events.jsonl data/processed.jsonl; do
  test -s "$f"
done
python3 - <<'PY'
import json
from pathlib import Path

from ci.score import evaluate_probe_window, validate_participant_submission

incident = json.loads(Path("evidence/incident.json").read_text())
submission = json.loads(Path("evidence/participant_submission.json").read_text())
probes = [
    json.loads(line)
    for line in Path("evidence/probe_results.jsonl").read_text().splitlines()
    if line.strip()
]
rows = [
    json.loads(line)
    for line in Path("data/processed.jsonl").read_text().splitlines()
    if line.strip()
]
events = [
    json.loads(line)
    for line in Path("data/events.jsonl").read_text().splitlines()
    if line.strip()
]

window = evaluate_probe_window(probes, incident["hidden_required_window_s"])
assert window["passed"], f"hidden health-stability window failed: {window}"
submission_check = validate_participant_submission(incident, submission)
assert submission_check["valid"], f"participant submission invalid: {submission_check}"
assert len(probes) >= 101
ids = [row["id"] for row in rows]
assert set(ids) == set(range(1, 9)) and len(ids) == len(set(ids))
assert any(event.get("event") == "crash" for event in events)
assert not Path("evidence/bash_history.txt").exists()
print("ASSERTIONS_PASS")
PY
