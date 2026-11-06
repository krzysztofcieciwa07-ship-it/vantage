"""Regression contract for valid GitHub expression syntax in CFR-18.

GitHub Actions string literals inside expressions require single quotes.
Invalid expressions result in failed workflow registrations with no jobs.
"""
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "cfr18.yml"


def test_cfr18_base_sha_fallback_is_a_valid_github_string_literal():
    source = WORKFLOW.read_text(encoding="utf-8")
    base_sha = next(line.strip() for line in source.splitlines()
                    if line.strip().startswith("BASE_SHA:"))
    expected = "BASE_SHA: " + "$" + "{{ github.event.pull_request.base.sha || '' }}"
    assert base_sha == expected, (
        "GitHub expression literals require single quotes; double quotes make "
        "the workflow fail before any jobs execute."
    )


def test_cfr18_keeps_required_security_and_runtime_gates():
    source = WORKFLOW.read_text(encoding="utf-8")
    for required in (
        "Unit tests",
        "Verify evidence chain",
        "Replay mutation",
        "Live forensic scenario",
        "Assert runtime evidence",
        "Generate forensic score",
        "Keyless sign external evidence anchor",
        "Independently verify signature and mutation rejection",
    ):
        assert required in source
