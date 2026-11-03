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
            "run_attempt": 1,
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


def test_independent_verifier_checkout_happens_before_evidence_download():
    """Checkout of main must not remove an already-downloaded evidence bundle."""
    from pathlib import Path
    workflow = (Path(__file__).resolve().parents[1] / ".github" / "workflows"
                / "provenance-independent.yml").read_text(encoding="utf-8")
    checkout = workflow.index("      - name: Checkout trusted verifier (default branch only)")
    download = workflow.index("      - name: Download evidence artifact from completed run")
    assert checkout < download, (
        "checkout after artifact download can delete provenance-bundle before verification"
    )
    assert "persist-credentials: false" in workflow
    assert "ref: main" in workflow


def test_cosign_v3_installer_is_pinned_and_shared_by_both_workflows():
    """The install action must support v3.1.3 Sigstore bundles in both CI jobs."""
    from pathlib import Path
    root = Path(__file__).resolve().parents[1] / '.github' / 'workflows'
    commit = 'b9c35392b7c1401bcc77d30c9b07cf4b1c7a7b07'
    for path in ('verify.yml', 'provenance-independent.yml'):
        text = (root / path).read_text(encoding='utf-8')
        assert 'uses: sigstore/cosign-installer@' + commit in text
        assert 'cosign-release: "v3.1.3"' in text


def test_resolver_binds_exact_workflow_run_attempt():
    v = event()
    v["workflow_run"]["run_attempt"] = 2
    assert resolve(v, REPO)["EXPECTED_RUN_ATTEMPT"] == "2"


def test_resolver_rejects_missing_or_invalid_run_attempt():
    for attempt in (None, 0, -1, "1", True):
        v = event()
        if attempt is None:
            v["workflow_run"].pop("run_attempt")
        else:
            v["workflow_run"]["run_attempt"] = attempt
        with pytest.raises(ValueError):
            resolve(v, REPO)
