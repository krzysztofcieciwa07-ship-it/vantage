import json
from .gen_incident import mutation
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
m=json.loads((ROOT/"evidence/incident.json").read_text())
assert mutation(m["seed"])==m["mutation"],"REPLAY FAIL: mutation mismatch"
print("REPLAY PASS: mutation manifest reproduced exactly")
