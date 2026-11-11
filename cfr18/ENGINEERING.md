# CFR-18 engineering boundary

CFR-18 is a separately provisioned forensic exercise within Vantage. It has its own Python dependencies, evidence fixtures, execution commands, and CI workflow.

## Operating rules

- Treat the lab as an isolated test environment. Do not point it at production systems or customer data.
- Keep secrets out of fixtures, evidence bundles, shell history, and logs.
- Use the exact source commit recorded by the workflow when evaluating evidence.
- Preserve the original evidence and record any mutation separately; do not silently rewrite a failed result.
- A deterministic incident, replay, or forensic score proves only the modeled scenario and checks that actually ran.
- Do not describe the lab as an endpoint security product, production incident response platform, or certified forensic process without separate evidence.

## Dependencies and verification

CFR-18 intentionally uses its own dependency set under this directory. From `cfr18/`, install `requirements.txt`, run `pytest -q`, and validate Compose with `docker compose config`. The GitHub Actions workflow is the source for the complete automated scenario; check its result against the exact PR head SHA before reporting success.

The repository-wide engineering and evidence vocabulary is defined in [../docs/ENGINEERING_STANDARD.md](../docs/ENGINEERING_STANDARD.md). This file documents the CFR-18 boundary and does not replace its test suite or independent evidence checks.

## Destructive local operations

The CFR-18 Makefile contains commands that remove local lab state:

- `make up` begins with `docker compose down -v --remove-orphans`, which removes Compose volumes before rebuilding the lab.
- `make down` removes Compose volumes and containers.
- `make clean` removes Compose volumes and deletes generated files under `data/` and `evidence/`.

Use only disposable lab data. Export and verify any evidence that must be retained before running these commands. Never run them against production services or a directory containing customer evidence. Generated CI artifacts are test evidence for the identified commit; they are not a substitute for an independently retained customer record.

