from pathlib import Path


def test_cfr18_base_sha_fallback_uses_valid_github_expression_literal():
    workflow = Path(".github/workflows/cfr18.yml").read_text(encoding="utf-8")
    assert "BASE_SHA: ${{ github.event.pull_request.base.sha || '' }}" in workflow
    assert 'BASE_SHA: ${{ github.event.pull_request.base.sha || "" }}' not in workflow
