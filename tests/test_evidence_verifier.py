from pathlib import Path
import hashlib
import os
import subprocess
import sys

def make_valid_evidence(path):
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    path.write_text(
        "commit=" + os.environ.get("GITHUB_SHA", "test-commit") + "\n"
        + "afe_vantage_sha256=" + sha("afe_vantage.py") + "\n"
        + "tests_sha256=" + sha("tests/test_afe_vantage.py") + "\n",
        encoding="utf-8",
    )

def run_verifier(path):
    env = dict(os.environ)
    env["GITHUB_SHA"] = os.environ.get("GITHUB_SHA", "test-commit")
    return subprocess.run(
        [sys.executable, "tools/verify_evidence.py", "--evidence", str(path)],
        capture_output=True, text=True, env=env,
    )

def test_independent_verifier_passes_for_current_evidence(tmp_path):
    evidence = tmp_path / "valid.txt"; make_valid_evidence(evidence)
    result = run_verifier(evidence)
    assert result.returncode == 0
    assert "INDEPENDENT_VERIFY: PASS" in result.stdout

def test_tampered_evidence_is_rejected(tmp_path):
    evidence = tmp_path / "tampered.txt"; make_valid_evidence(evidence)
    text = evidence.read_text(encoding="utf-8")
    evidence.write_text(text.replace("afe_vantage_sha256=", "afe_vantage_sha256=0", 1), encoding="utf-8")
    result = run_verifier(evidence)
    assert result.returncode != 0
    assert "afe_vantage_sha256 mismatch" in result.stderr

def test_false_commit_provenance_is_rejected(tmp_path):
    evidence = tmp_path / "false-commit.txt"; make_valid_evidence(evidence)
    text = evidence.read_text(encoding="utf-8")
    current = os.environ.get("GITHUB_SHA", "test-commit")
    evidence.write_text(text.replace("commit=" + current, "commit=FALSE_COMMIT", 1), encoding="utf-8")
    result = run_verifier(evidence)
    assert result.returncode != 0
    assert "commit mismatch" in result.stderr
