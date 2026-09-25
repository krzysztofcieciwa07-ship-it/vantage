from ci.adaptive_window import required_window
from ci.gen_incident import mutation
from ci.evidence_vault import canon
import json

def test_window_deterministic_and_adaptive():
    assert required_window(12345, 0) == required_window(12345, 0)
    assert required_window(12345, 3600) >= required_window(12345, 1800)
    assert required_window(12345, 10000) <= 300

def test_mutation_deterministic():
    assert mutation(12345) == mutation(12345)
    assert mutation(1)["variant"] in {"double_process", "silent_loss", "reactivation"}

def test_chain_canonicalization_is_stable():
    a={"b":2,"a":1}
    assert canon(a) == json.dumps(a,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
