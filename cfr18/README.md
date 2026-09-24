# CFR-18 — Queue Resurrection

Isolated forensic exercise inside Vantage. It lives under cfr18/ and does not modify the existing Vantage runtime.

## Run
```bash
cd cfr18
python3 -m pytest -q
python3 -m ci.evidence_vault verify
python3 -m ci.gen_incident --seed 12345
python3 -m ci.replay
```

The local vault is tamper-evident, not immutable. Final forensic verification requires an external CI/signature anchor.
