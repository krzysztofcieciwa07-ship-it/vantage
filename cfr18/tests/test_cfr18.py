from ci.adaptive_window import required_window
from ci.gen_incident import build_incident, mutation
from ci.evidence_vault import canon
import json


def test_window_deterministic_and_adaptive():
    assert required_window(12345, 0) == required_window(12345, 0)
    assert required_window(12345, 3600) >= required_window(12345, 1800)
    assert required_window(12345, 10000) <= 300


def test_mutation_deterministic():
    assert mutation(12345) == mutation(12345)
    assert mutation(1)["variant"] in {"double_process", "silent_loss", "reactivation"}


def test_generated_incident_declares_the_actual_evidence_contract():
    incident = build_incident(12345, "2026-11-08T22:29:22.661304+00:00")

    assert incident["required_evidence"] == [
        "evidence/.chain.jsonl",
        "evidence/incident.json",
        "evidence/manifest.json",
        "evidence/probe_results.jsonl",
        "evidence/participant_submission.json",
        "evidence/score_result.json",
        "data/events.jsonl",
        "data/processed.jsonl",
    ]


def test_chain_canonicalization_is_stable():
    a = {"b": 2, "a": 1}
    assert canon(a) == json.dumps(
        a, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()
