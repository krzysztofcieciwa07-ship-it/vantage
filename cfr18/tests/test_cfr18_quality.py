from datetime import datetime, timedelta, timezone
import json

from ci import score


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


def healthy_probes(count: int):
    start = datetime(2026, 11, 3, tzinfo=timezone.utc)
    return [
        {
            "ts": (start + timedelta(seconds=index)).isoformat(),
            "status": "ok",
        }
        for index in range(count)
    ]


def participant_submission(fault_type: str = "double_process", source: str = "participant"):
    return {
        "schema": "CFR-18/participant-submission-v1",
        "source": source,
        "fault_type": fault_type,
        "root_cause": (
            "The worker crashed after dequeuing a job. Restart replayed work, "
            "so processing must be idempotent by job identifier."
        ),
        "evidence_refs": [
            "data/events.jsonl#event=crash",
            "data/processed.jsonl#id=8",
        ],
        "reported_at": "2026-11-03T02:30:00+00:00",
    }


def incident_fixture():
    return {
        "mutation": {"variant": "double_process"},
        "required_evidence": REQUIRED_EVIDENCE,
    }


def write_evidence(root):
    data = root / "data"
    data.mkdir(parents=True, exist_ok=True)
    (data / "events.jsonl").write_text(
        json.dumps({"event": "crash", "id": 4}) + "\n"
    )
    (data / "processed.jsonl").write_text(
        json.dumps({"id": 8, "status": "done"}) + "\n"
    )
    return root


def test_probe_success_ratio_reports_only_sampled_health_checks():
    probes = healthy_probes(4)
    probes[1]["status"] = "fail"

    assert score.probe_success_ratio(probes) == 0.75
    assert score.probe_success_ratio([]) == 0.0


def test_probe_window_does_not_round_a_short_duration_up_to_the_threshold():
    probes = healthy_probes(136)
    start = datetime.fromisoformat(probes[0]["ts"])
    duration = 134.9996
    for index, probe in enumerate(probes):
        probe["ts"] = (
            start + timedelta(seconds=duration * index / 135)
        ).isoformat()

    result = score.evaluate_probe_window(probes, 135)

    assert result["observed_window_s"] == 135.0
    assert result["passed"] is False


def test_probe_window_does_not_round_a_gap_over_two_seconds_down_to_two():
    probes = healthy_probes(136)
    start = datetime.fromisoformat(probes[0]["ts"])
    total_duration = 135.0
    special_gap = 2.0004
    normal_gap = (total_duration - special_gap) / 134
    elapsed = 0.0
    for index, probe in enumerate(probes):
        if index:
            elapsed += special_gap if index == 50 else normal_gap
        probe["ts"] = (start + timedelta(seconds=elapsed)).isoformat()

    result = score.evaluate_probe_window(probes, 135)

    assert result["max_gap_s"] == 2.0
    assert result["passed"] is False


def test_ci_reference_fixture_is_not_awarded_human_diagnosis_points():
    submission = participant_submission(source="CI_REFERENCE_FIXTURE")
    result = score.participant_scoring_adjustment(
        submission, {"fault_type_correct": True}
    )

    assert result == {
        "fault_type_correct": None,
        "score_adjustment": 0.0,
        "status": "REFERENCE_FIXTURE_NOT_GRADED",
    }


def test_human_participant_classification_is_scored_separately_from_ci_fixture():
    correct = score.participant_scoring_adjustment(
        participant_submission(source="participant"),
        {"fault_type_correct": True},
    )
    incorrect = score.participant_scoring_adjustment(
        participant_submission("silent_loss", source="participant"),
        {"fault_type_correct": False},
    )

    assert correct == {
        "fault_type_correct": True,
        "score_adjustment": 0.03,
        "status": "GRADED",
    }
    assert incorrect == {
        "fault_type_correct": False,
        "score_adjustment": -0.01,
        "status": "GRADED",
    }


def test_probe_window_rejects_120_samples_for_a_135_second_requirement():
    result = score.evaluate_probe_window(healthy_probes(120), 135)

    assert result == {
        "passed": False,
        "required_window_s": 135,
        "observed_window_s": 119,
        "sample_count": 120,
        "max_gap_s": 1.0,
        "all_healthy": True,
    }


def test_probe_window_passes_only_after_full_required_duration():
    result = score.evaluate_probe_window(healthy_probes(136), 135)

    assert result == {
        "passed": True,
        "required_window_s": 135,
        "observed_window_s": 135,
        "sample_count": 136,
        "max_gap_s": 1.0,
        "all_healthy": True,
    }


def test_probe_window_accepts_134_samples_when_full_coverage_and_gap_limit_hold():
    probes = healthy_probes(134)
    start = datetime.fromisoformat(probes[0]["ts"])
    elapsed = 0
    for index in range(1, len(probes)):
        elapsed += 2 if index in (40, 90) else 1
        probes[index]["ts"] = (start + timedelta(seconds=elapsed)).isoformat()

    result = score.evaluate_probe_window(probes, 135)

    assert result == {
        "passed": True,
        "required_window_s": 135,
        "observed_window_s": 135,
        "sample_count": 134,
        "max_gap_s": 2.0,
        "all_healthy": True,
    }


def test_probe_window_rejects_sparse_samples_even_when_first_and_last_cover_window():
    probes = healthy_probes(135)
    for index in range(40, len(probes)):
        ts = datetime.fromisoformat(probes[index]["ts"])
        probes[index]["ts"] = (ts + timedelta(seconds=2)).isoformat()

    result = score.evaluate_probe_window(probes, 135)

    assert result["passed"] is False
    assert result["observed_window_s"] == 136
    assert result["max_gap_s"] == 3.0


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
    result = score.validate_participant_submission(incident_fixture(), None)

    assert result == {
        "valid": False,
        "fault_type_correct": False,
        "reason": "missing_submission",
    }


def test_participant_submission_is_compared_with_incident_not_generated_from_it(tmp_path):
    root = write_evidence(tmp_path)
    correct = score.validate_participant_submission(
        incident_fixture(), participant_submission("double_process"), evidence_root=root
    )
    incorrect = score.validate_participant_submission(
        incident_fixture(), participant_submission("silent_loss"), evidence_root=root
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


def test_participant_submission_references_must_resolve_to_real_records(tmp_path):
    root = write_evidence(tmp_path)
    submission = participant_submission()
    submission["evidence_refs"] = ["data/events.jsonl#event=missing"]

    result = score.validate_participant_submission(
        incident_fixture(), submission, evidence_root=root
    )

    assert result == {
        "valid": False,
        "fault_type_correct": False,
        "reason": "unresolved_evidence_reference",
    }


def test_participant_submission_rejects_missing_evidence_file(tmp_path):
    root = tmp_path
    (root / "data").mkdir()
    (root / "data" / "events.jsonl").write_text(
        json.dumps({"event": "crash"}) + "\n"
    )
    submission = participant_submission()

    result = score.validate_participant_submission(
        incident_fixture(), submission, evidence_root=root
    )

    assert result["valid"] is False
    assert result["reason"] == "unresolved_evidence_reference"


def test_participant_submission_rejects_path_traversal_in_evidence_reference(tmp_path):
    root = write_evidence(tmp_path)
    submission = participant_submission()
    submission["evidence_refs"] = ["../outside.jsonl#event=crash"]

    result = score.validate_participant_submission(
        incident_fixture(), submission, evidence_root=root
    )

    assert result["valid"] is False
    assert result["reason"] == "unresolved_evidence_reference"


def test_participant_submission_rejects_unknown_source_label(tmp_path):
    root = write_evidence(tmp_path)
    submission = participant_submission(source="automation_claiming_human")

    result = score.validate_participant_submission(
        incident_fixture(), submission, evidence_root=root
    )

    assert result["valid"] is False
    assert result["reason"] == "invalid_submission_source"


def test_empty_root_cause_or_evidence_references_are_rejected(tmp_path):
    root = write_evidence(tmp_path)
    report = participant_submission()
    report["root_cause"] = ""
    report["evidence_refs"] = []

    result = score.validate_participant_submission(
        incident_fixture(), report, evidence_root=root
    )

    assert result["valid"] is False
    assert result["reason"] == "incomplete_submission"
