import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .adaptive_window import required_window
from .evidence_vault import append

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_EVIDENCE = [
    "evidence/.chain.jsonl",
    "evidence/incident.json",
    "evidence/manifest.json",
    "evidence/probe_results.jsonl",
    "evidence/participant_submission.json",
    "evidence/score_result.json",
    "data/events.jsonl",
    "data/processed.jsonl",
]


def mutation(seed: int):
    value = int(hashlib.sha256(f"CFR18:{seed}".encode()).hexdigest()[:16], 16)
    variants = ("double_process", "double_process", "silent_loss", "reactivation")
    return {
        "seed": seed,
        "variant": variants[value % 4],
        "kill_delay_ms": 250 + value % 1750,
        "queue_depth": 25 + value % 76,
    }


def build_incident(seed: int, opened_at: str) -> dict:
    mutation_spec = mutation(seed)
    return {
        "schema": "CFR-18/1",
        "ticket_id": f"CFR18-{seed:08d}",
        "opened_at": opened_at,
        "seed": seed,
        "mutation": mutation_spec,
        "hidden_required_window_s": required_window(seed),
        "required_evidence": list(REQUIRED_EVIDENCE),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()

    now = datetime.now(timezone.utc).isoformat()
    incident = build_incident(args.seed, now)

    evidence_dir = ROOT / "evidence"
    evidence_dir.mkdir(exist_ok=True)
    incident_path = evidence_dir / "incident.json"
    incident_path.write_text(json.dumps(incident, indent=2) + "\n")

    manifest = {
        "schema": "CFR-18/evidence-manifest-v1",
        "session_seed": args.seed,
        "incident_sha256": hashlib.sha256(incident_path.read_bytes()).hexdigest(),
        "created_at": now,
    }
    (evidence_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    append(
        "incident_created",
        {
            "ticket_id": incident["ticket_id"],
            "seed": args.seed,
            "variant": incident["mutation"]["variant"],
        },
    )
    print(json.dumps(incident, indent=2))


if __name__ == "__main__":
    main()
