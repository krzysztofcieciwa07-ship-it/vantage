import json
from datetime import datetime, timezone
from pathlib import Path

from .evidence_vault import verify_chain, verify_bound_files

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "evidence"
MAX_PROBE_GAP_S = 2.0
CI_REFERENCE_SOURCE = "CI_REFERENCE_FIXTURE"
ALLOWED_SUBMISSION_SOURCES = {CI_REFERENCE_SOURCE, "participant"}
ALLOWED_EVIDENCE_REFERENCE_FILES = {
    "data/events.jsonl",
    "data/processed.jsonl",
}


def read_jsonl(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def probe_success_ratio(probes):
    """Return the fraction of recorded health probes that succeeded.

    This metric describes only the sampled probe set. It is not end-to-end
    service availability, incident uptime, or a substitute for MTTR.
    """
    if not isinstance(probes, list) or not probes:
        return 0.0
    successful = sum(
        isinstance(probe, dict) and probe.get("status") == "ok"
        for probe in probes
    )
    return round(successful / len(probes), 4)


def _parse_timestamp(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def evaluate_probe_window(probes, required_window_s):
    """Require a healthy full-duration window with no sampling gap over two seconds."""
    try:
        required = int(required_window_s)
    except (TypeError, ValueError):
        required = 0

    sample_count = len(probes) if isinstance(probes, list) else 0
    all_healthy = (
        sample_count > 0
        and all(
            isinstance(probe, dict) and probe.get("status") == "ok"
            for probe in probes
        )
    )

    timestamps = []
    timestamps_valid = sample_count > 0
    if timestamps_valid:
        for probe in probes:
            parsed = _parse_timestamp(probe.get("ts")) if isinstance(probe, dict) else None
            if parsed is None:
                timestamps_valid = False
                break
            timestamps.append(parsed)

    monotonic = timestamps_valid and all(
        current > previous
        for previous, current in zip(timestamps, timestamps[1:])
    )
    gaps = [
        (current - previous).total_seconds()
        for previous, current in zip(timestamps, timestamps[1:])
    ] if monotonic else []
    raw_max_gap_s = max(gaps) if gaps else None
    raw_observed_window_s = (
        (timestamps[-1] - timestamps[0]).total_seconds()
        if monotonic and len(timestamps) >= 2
        else None
    )

    # Compare full-precision values. Rounding is for display only and must
    # never turn 134.9996s into a passing 135.000s window or 2.0004s into
    # an acceptable 2.000s sample gap.
    passed = (
        required > 0
        and sample_count >= 2
        and all_healthy
        and monotonic
        and raw_observed_window_s is not None
        and raw_observed_window_s >= required
        and raw_max_gap_s is not None
        and raw_max_gap_s <= MAX_PROBE_GAP_S
    )
    return {
        "passed": passed,
        "required_window_s": required,
        "observed_window_s": round(raw_observed_window_s, 3) if raw_observed_window_s is not None else None,
        "sample_count": sample_count,
        "max_gap_s": round(raw_max_gap_s, 3) if raw_max_gap_s is not None else None,
        "all_healthy": all_healthy,
    }


def _evidence_reference_resolves(reference, incident, evidence_root):
    """Resolve a field=value pointer to a real JSONL record in declared runtime evidence."""
    if not isinstance(reference, str) or reference.count("#") != 1:
        return False
    relative_path, selector = reference.split("#", 1)
    if relative_path not in ALLOWED_EVIDENCE_REFERENCE_FILES:
        return False

    declared = (incident or {}).get("required_evidence", [])
    if not isinstance(declared, list) or relative_path not in declared:
        return False

    if selector.count("=") != 1:
        return False
    field, expected_value = selector.split("=", 1)
    if not field or not expected_value:
        return False

    root = Path(evidence_root).resolve()
    target = (root / relative_path).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return False
    if not target.is_file():
        return False

    try:
        lines = target.read_text().splitlines()
    except (OSError, UnicodeError):
        return False

    for line in lines:
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            return False
        if not isinstance(row, dict):
            return False
        if field in row and str(row[field]) == expected_value:
            return True
    return False


def validate_participant_submission(incident, submission, evidence_root=ROOT):
    """Validate a separate participant report and resolve every evidence pointer."""
    if submission is None:
        return {
            "valid": False,
            "fault_type_correct": False,
            "reason": "missing_submission",
        }
    if not isinstance(submission, dict):
        return {
            "valid": False,
            "fault_type_correct": False,
            "reason": "invalid_submission_schema",
        }

    if submission.get("schema") != "CFR-18/participant-submission-v1":
        return {
            "valid": False,
            "fault_type_correct": False,
            "reason": "invalid_submission_schema",
        }

    source = submission.get("source")
    if not isinstance(source, str) or source not in ALLOWED_SUBMISSION_SOURCES:
        return {
            "valid": False,
            "fault_type_correct": False,
            "reason": "invalid_submission_source",
        }

    root_cause = submission.get("root_cause")
    evidence_refs = submission.get("evidence_refs")
    submitted_at = _parse_timestamp(submission.get("reported_at"))
    fault_type = submission.get("fault_type")
    expected_fault = (incident or {}).get("mutation", {}).get("variant")

    if (
        not isinstance(root_cause, str)
        or len(root_cause.strip()) < 20
        or not isinstance(evidence_refs, list)
        or not evidence_refs
        or submitted_at is None
        or not isinstance(fault_type, str)
        or not fault_type.strip()
        or not isinstance(expected_fault, str)
        or not expected_fault
    ):
        return {
            "valid": False,
            "fault_type_correct": False,
            "reason": "incomplete_submission",
        }

    if any(
        not _evidence_reference_resolves(reference, incident, evidence_root)
        for reference in evidence_refs
    ):
        return {
            "valid": False,
            "fault_type_correct": False,
            "reason": "unresolved_evidence_reference",
        }

    correct = fault_type == expected_fault
    return {
        "valid": True,
        "fault_type_correct": correct,
        "reason": "ok" if correct else "fault_type_mismatch",
    }


def participant_scoring_adjustment(submission, submission_check):
    """Do not grade or award diagnosis points to the deterministic CI fixture."""
    if submission.get("source") == CI_REFERENCE_SOURCE:
        return {
            "fault_type_correct": None,
            "score_adjustment": 0.0,
            "status": "REFERENCE_FIXTURE_NOT_GRADED",
        }
    if submission.get("source") != "participant":
        return {
            "fault_type_correct": None,
            "score_adjustment": 0.0,
            "status": "UNKNOWN_SOURCE_NOT_GRADED",
        }

    correct = bool(submission_check.get("fault_type_correct"))
    return {
        "fault_type_correct": correct,
        "score_adjustment": 0.03 if correct else -0.01,
        "status": "GRADED",
    }


def score():
    chain = verify_chain()
    if not chain["valid"]:
        raise SystemExit("SCORE VOID: evidence chain tampered")
    bound, reason = verify_bound_files()
    if not bound:
        raise SystemExit("SCORE VOID: " + reason)

    probes = read_jsonl(EV / "probe_results.jsonl")
    processed = read_jsonl(ROOT / "data/processed.jsonl")
    events = read_jsonl(ROOT / "data/events.jsonl")
    incident_path = EV / "incident.json"
    submission_path = EV / "participant_submission.json"

    if not incident_path.is_file():
        raise SystemExit("SCORE BLOCKED: incident evidence missing")
    if not submission_path.is_file():
        raise SystemExit("SCORE BLOCKED: participant submission missing")

    incident = json.loads(incident_path.read_text())
    submission = json.loads(submission_path.read_text())
    required_window_s = incident.get("hidden_required_window_s")
    window = evaluate_probe_window(probes, required_window_s)
    if not window["passed"]:
        raise SystemExit(
            "SCORE BLOCKED: hidden stability window incomplete "
            f"(required={window['required_window_s']}s, "
            f"observed={window['observed_window_s']}s, "
            f"max_gap={window['max_gap_s']}s, "
            f"samples={window['sample_count']}, "
            f"all_healthy={window['all_healthy']})"
        )

    submission_check = validate_participant_submission(incident, submission)
    if not submission_check["valid"]:
        raise SystemExit(
            "SCORE BLOCKED: participant submission invalid "
            f"({submission_check['reason']})"
        )

    classification = participant_scoring_adjustment(submission, submission_check)
    sampled_health_ratio = probe_success_ratio(probes)
    ids = [row.get("id") for row in processed]
    unique = set(ids)
    duplicates = max(0, len(ids) - len(unique))
    recovered = len(unique & set(range(1, 9))) / 8
    crashes = sum(event.get("event") == "crash" for event in events)

    # Automated runtime-recovery score only. This ratio covers the post-recovery
    # health probes, not service uptime across the whole incident. No MTTR is
    # calculated because the runtime event log does not capture event timestamps.
    # No operator-investigation points are awarded without an independent trace.
    base = (
        0.20 * sampled_health_ratio
        + 0.25 * recovered
        + 0.20 * (1 - min(duplicates / 8, 1))
        + 0.10 * (1 if crashes else 0)
    )
    total = max(0, min(1, base + classification["score_adjustment"]))
    result = {
        "schema": "CFR-18/forensic-score-v3",
        "score_scope": "automated_runtime_recovery",
        "status": "MERIT" if total >= 0.75 else ("PASS" if total >= 0.60 else "FAIL"),
        "score": round(total, 4),
        "submission_source": submission.get("source"),
        "metrics": {
            "probe_success_ratio": sampled_health_ratio,
            "probe_scope": "post_recovery_stability_window_only",
            "recovered_job_fraction": round(recovered, 4),
            "duplicate_records": duplicates,
            "crash_events": crashes,
            "mttr_status": "NOT_CAPTURED",
            "probe_samples": window["sample_count"],
            "required_window_s": window["required_window_s"],
            "observed_window_s": window["observed_window_s"],
            "max_probe_gap_s": window["max_gap_s"],
            "health_window_passed": window["passed"],
            "participant_submission_valid": submission_check["valid"],
            "participant_classification_status": classification["status"],
            "participant_score_adjustment": classification["score_adjustment"],
            "fault_type_correct": classification["fault_type_correct"],
            "investigation_quality": None,
            "operator_trace_status": "NOT_CAPTURED",
        },
        "chain_root_before_score": chain["root"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    (EV / "score_result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    print(json.dumps(score(), indent=2))
