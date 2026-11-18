from pathlib import Path


def test_cfr18_base_sha_fallback_uses_valid_github_expression_literal():
    workflow = Path(".github/workflows/cfr18.yml").read_text(encoding="utf-8")
    assert "BASE_SHA: ${{ github.event.pull_request.base.sha || '' }}" in workflow
    assert 'BASE_SHA: ${{ github.event.pull_request.base.sha || "" }}' not in workflow


def test_cfr18_checks_out_and_asserts_exact_source_head_sha():
    workflow = Path(".github/workflows/cfr18.yml").read_text(encoding="utf-8")
    assert "ref: ${{ github.event.pull_request.head.sha || github.sha }}" in workflow
    assert "test \"$(git rev-parse HEAD)\" = \"$SOURCE_HEAD_SHA\"" in workflow


def test_cfr18_anchor_separates_source_base_and_workflow_event_shas():
    workflow = Path(".github/workflows/cfr18.yml").read_text(encoding="utf-8")
    assert '"commit": os.environ["SOURCE_HEAD_SHA"]' in workflow
    assert '"base_sha": os.environ["BASE_SHA"]' in workflow
    assert '"workflow_run_commit": os.environ["GITHUB_SHA"]' in workflow
