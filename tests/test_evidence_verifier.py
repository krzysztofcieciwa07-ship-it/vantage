import hashlib
import json
import subprocess
import sys

def test_hash_anchored_provenance_passes(tmp_path):
    evidence=tmp_path/"evidence.txt"; replay=tmp_path/"replay.json"; anchor=tmp_path/"anchor.json"
    evidence.write_text("commit=test-commit\n"); replay.write_text('{"verdict":"BLOCK"}\n')
    subprocess.run([sys.executable,"tools/provenance_anchor.py","build","--commit","test-commit","--evidence",str(evidence),"--replay",str(replay),"--output",str(anchor)],check=True)
    result=subprocess.run([sys.executable,"tools/provenance_anchor.py","verify","--anchor",str(anchor),"--expected-commit","test-commit"],capture_output=True,text=True)
    assert result.returncode==0 and "PROVENANCE_ANCHOR: PASS" in result.stdout

def test_hash_anchor_rejects_mutation(tmp_path):
    evidence=tmp_path/"evidence.txt"; replay=tmp_path/"replay.json"; anchor=tmp_path/"anchor.json"
    evidence.write_text("commit=test-commit\n"); replay.write_text('{"verdict":"BLOCK"}\n')
    subprocess.run([sys.executable,"tools/provenance_anchor.py","build","--commit","test-commit","--evidence",str(evidence),"--replay",str(replay),"--output",str(anchor)],check=True)
    data=json.loads(anchor.read_text()); data["replay_sha256"]=hashlib.sha256(b"tampered").hexdigest(); anchor.write_text(json.dumps(data)+"\n")
    result=subprocess.run([sys.executable,"tools/provenance_anchor.py","verify","--anchor",str(anchor),"--expected-commit","test-commit"],capture_output=True,text=True)
    assert result.returncode!=0 and "record_hash mismatch" in result.stderr
