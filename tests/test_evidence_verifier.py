from pathlib import Path
import os, subprocess, sys, hashlib

def test_independent_verifier_passes_for_current_evidence():
    evidence=Path("evidence/vantage-verification.txt"); evidence.parent.mkdir(exist_ok=True)
    h=lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    evidence.write_text("commit="+os.environ.get("GITHUB_SHA","test-commit")+"\nafe_vantage_sha256="+h("afe_vantage.py")+"\ntests_sha256="+h("tests/test_afe_vantage.py")+"\n",encoding="utf-8")
    env=dict(os.environ); env["GITHUB_SHA"]=os.environ.get("GITHUB_SHA","test-commit")
    result=subprocess.run([sys.executable,"tools/verify_evidence.py"],capture_output=True,text=True,env=env)
    assert result.returncode==0
    assert "INDEPENDENT_VERIFY: PASS" in result.stdout
