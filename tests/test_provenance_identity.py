import pytest
from tools.provenance_identity import resolve

REPO = "krzysztofcieciwa07-ship-it/vantage"
SHA = "f" * 40


def event(kind="pull_request", prs=None, branch="feature/harden"):
    return {
        "repository": {"full_name": REPO},
        "workflow_run": {
            "repository": {"full_name": REPO},
            "name": "Vantage Verify",
            "status": "completed",
            "conclusion": "success",
            "event": kind,
            "head_sha": SHA,
            "head_branch": branch,
            "id": 40968975127,
            "pull_requests": [{"number": 8}] if prs is None else prs,
        },
    }


def test_pull_request_identity_exact():
    got = resolve(event(), REPO)
    assert got["EXPECTED_IDENTITY"] == f"https://github.com/{REPO}/.github/workflows/verify.yml@refs/pull/8/merge"
    assert got["EXPECTED_COMMIT"] == SHA
    assert got["EXPECTED_RUN_ID"] == "40968975127"


def test_main_push_identity_exact():
    got = resolve(event("push", [], "main"), REPO)
    assert got["EXPECTED_IDENTITY"].endswith("@refs/heads/main")


def test_manual_main_identity_exact():
    assert resolve(event("workflow_dispatch", [], "main"), REPO)["EXPECTED_IDENTITY"].endswith("@refs/heads/main")


@pytest.mark.parametrize("payload", [
    event("pull_request", []),
    event("pull_request", [{"number": 8}, {"number": 9}]),
    event("pull_request", [{"number": "8"}]),
    event("push", [], "untrusted-branch"),
    event("workflow_dispatch", [], "untrusted-branch"),
    event("evil", []),
])
def test_ambiguous_or_unsupported_context_fails_closed(payload):
    with pytest.raises(ValueError):
        resolve(payload, REPO)


def test_wrong_repository_fails_closed():
    with pytest.raises(ValueError):
        resolve(event(), "another-owner/repo")


def test_untrusted_workflow_or_unsuccessful_run_fails_closed():
    for change in ({"name": "Not Vantage Verify"}, {"conclusion": "failure"},
                   {"head_sha": "0" * 39}, {"id": 0}):
        data = event()
        data["workflow_run"].update(change)
        with pytest.raises(ValueError):
            resolve(data, REPO)
