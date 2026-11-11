# Contributing to Vantage

Vantage is currently classified as a prototype. Contributions must preserve that boundary in code, tests, documentation, and release claims.

## Before changing code

1. Read README.md, SECURITY.md, and docs/ENGINEERING_STANDARD.md.
2. Identify the behavior and trust boundary affected by the change.
3. Keep changes focused and add regression tests for defects.
4. Never commit API keys, credentials, customer data, generated run evidence, or private logs.

## Root development setup

Use Python 3.12 or newer:

~~~bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
~~~

On Windows PowerShell, activate with .venv/Scripts/Activate.ps1.

## Root verification

Run from the repository root:

~~~bash
python -m pytest -q
python run_e2e.py
python run_hybrid_e2e.py
python tools/adversarial_matrix.py
~~~

The root demo uses deterministic providers unless an explicitly configured provider is used. A deterministic test run is not a live LLM call or proof of detector effectiveness.

## CFR-18 exercise

The CFR-18 lab has an independent dependency set and operational requirements:

~~~bash
cd cfr18
python -m pip install -r requirements.txt
python -m pytest -q
docker compose config
~~~

Review cfr18/README.md and its Makefile before running live or destructive lab scenarios. Do not point the lab at production infrastructure.

## Pull requests

- Use a focused branch and descriptive commit messages.
- Include the exact candidate SHA and links to the actual workflow runs.
- Report failures, skipped checks, and unavailable prerequisites.
- Do not describe deterministic simulations as live provider verification.
- Do not describe the digest-based synthetic stability score as an execution sandbox.
- Do not claim production readiness without independent runtime evidence and a real security review.
