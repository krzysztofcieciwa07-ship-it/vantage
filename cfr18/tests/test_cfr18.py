from ci.adaptive_window import required_window
from ci.gen_incident import mutation
def test_window_deterministic(): assert required_window(12345)==required_window(12345) and 100<=required_window(12345)<=300
def test_mutation_deterministic(): assert mutation(12345)==mutation(12345) and mutation(1)["variant"] in {"double_process","silent_loss","reactivation"}
