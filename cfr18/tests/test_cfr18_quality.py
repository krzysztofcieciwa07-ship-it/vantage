from datetime import datetime, timedelta, timezone

from ci import score


def healthy_probes(count: int):
    start = datetime(2026, 11, 3, tzinfo=timezone.utc)
    return [
        {
            "ts": (start + timedelta(seconds=index)).isoformat(),
            "status": "ok",
        }
        for index in range(count)
    ]


def participant_submission(fault_type: str = "double_process"):
    return {
        "schema": "CFR-18/participant-submission-v1",
        "source": "test_fixture",
        "fault_type": fault_type,
        "root_cause": (
            "The worker crashed after dequeuing a job. Restart replayed work, "
            "so processing must be idempotent by job identifier."
        ),
        "evidence_refs": ["data/events.jsonl#crash", "data/processed.jsonl#job-id"],
        "reported_at": "2026-11-03T02:30:00+00:00",
    }


def test_probe_window_rejects_120_samples_for_a_135_second_requirement():
    result = score.evaluate_probe_window(healthy_probes(120), 135)

    assert result == {
        "passed": False,
        "required_window_s": 135,
        "observed_window_s": 119,
        "sample_count": 120,
        "all_healthy": True,
    }


def test_probe_window_passes_only_after_full_required_duration():
    result = score.evaluate_probe_window(healthy_probes(136), 135)

    assert result == {
        "passed": True,
        "required_window_s": 135,
        "observed_window_s": 135,
        "sample_count": 136,
        "all_healthy": True,
    }


def test_probe_window_fails_when_a_health_sample_fails():
    probes = healthy_probes(136)
    probes[72]["status"] = "fail"

    result = score.evaluate_probe_window(probes, 135)

    assert result["passed"] is False
    assert result["all_healthy"] is False


def test_probe_window_fails_when_timestamps_are_missing_or_not_monotonic():
    probes = healthy_probes(136)
    probes[25]["ts"] = "not-a-timestamp"

    malformed = score.evaluate_probe_window(probes, 135)
    assert malformed["passed"] is False

    probes = healthy_probes(136)
    probes[25], probes[26] = probes[26], probes[25]
    unordered = score.evaluate_probe_window(probes, 135)
    assert unordered["passed"] is False


def test_participant_submission_must_be_a_separate_structured_input():
    incident = {"mutation": {"variant": "double_process"}}

    result = score.validate_participant_submission(incident, None)

    assert result == {
        "valid": False,
        "fault_type_correct": False,
        "reason": "missing_submission",
    }


def test_participant_submission_is_compared_with_incident_not_generated_from_it():
    incident = {"mutation": {"variant": "double_process"}}

    correct = score.validate_participant_submission(
        incident, participant_submission("double_process")
    )
    incorrect = score.validate_participant_submission(
        incident, participant_submission("silent_loss")
    )

    assert correct == {
        "valid": True,
        "fault_type_correct": True,
        "reason": "ok",
    }
    assert incorrect == {
        "valid": True,
        "fault_type_correct": False,
        "reason": "fault_type_mismatch",
    }


def test_empty_root_cause_or_evidence_references_are_rejected():
    incident = {"mutation": {"variant": "double_process"}}
    report = participant_submission()
    report["root_cause"] = ""
    report["evidence_refs"] = []

    result = score.validate_participant_submission(incident, report)

    assert result["valid"] is False
    assert result["reason"] == "incomplete_submission"
