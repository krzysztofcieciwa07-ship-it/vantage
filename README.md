# Vantage — execution-risk gate prototype

Vantage is a **prototype** for detecting risky instructions, routing a task through a deterministic decision gate, and optionally invoking an LLM provider only after the gate returns `ALLOW`. The repository also contains a small CFR-18 forensic exercise.

This README describes the code present on the repository's `main` baseline. A workflow definition, local test, or deterministic simulation is not proof of production deployment or comprehensive security.

## Repository contents

| Path | Actual role |
|---|---|
| `afe_vantage.py` | Main AFE/Vantage prototype: text-pattern detection, Unicode normalization, one-layer Base64 inspection, deterministic synthetic stability score, incident score, source trust weights, and ALLOW/HUMAN_APPROVAL/BLOCK decision. |
| `llm_runtime.py` | OpenAI-compatible HTTP provider, deterministic test provider, fallback wrapper, and LLM runtime behind the AFE decision. |
| `hybrid_runtime.py` | Two-provider wrapper. It compares exact output strings and withholds a conflicting result for human review. |
| `run_e2e.py`, `run_hybrid_e2e.py` | Deterministic end-to-end demonstrations using test providers. |
| `tests/` | Unit and contract tests for the gate, LLM wrappers, adversarial inputs, and evidence verifier. |
| `tools/` | Adversarial matrix, provenance-anchor and evidence-verification helpers. |
| `cfr18/` | Separate CFR-18 incident/forensic exercise with Docker Compose services, probe/load/tamper scripts, evidence vault, scoring and tests. |
| `.github/workflows/` | Verification, CFR-18, and independent-provenance workflow definitions. |
| `E2E_HYBRID_PROOF.txt` | Small proof note; inspect its contents and exact commit before treating it as runtime evidence. |

## Important implementation limits

- The `sandbox()` method in `afe_vantage.py` calculates a deterministic value from a SHA-256 digest. It does **not** execute code in an isolated sandbox or measure runtime stability.
- The detector is a finite pattern/normalization heuristic. It is not a trained classifier, complete prompt-injection detector, or guarantee against novel/adversarial inputs.
- Source trust weights and the in-memory block counter are prototype policy inputs, not a validated risk model or durable reputation system.
- `LLMRuntime` uses an OpenAI-compatible HTTP API when configured. CI demonstrations use `DeterministicProvider`; these do not prove a live model call.
- `HybridLLMRuntime` tests exact text equality between provider outputs. Agreement does not establish factual correctness or independent verification.
- The fallback wrapper can switch to a deterministic provider after a primary provider exception. A successful fallback is not evidence that the primary model was available.
- CFR-18 is a separate exercise inside this repository. Its presence does not establish that the larger Vantage product or a hosted range is deployed securely.

## Decision contract

- `ALLOW` — the prototype permits the next step.
- `HUMAN_APPROVAL` — the prototype withholds the next step for human review.
- `BLOCK` — the prototype denies the next step.

Do not interpret these labels as production authorization without an independently authenticated policy and approval boundary.

## CI verification

The workflow `.github/workflows/verify.yml` checks out the event's exact source SHA, installs pytest, runs tests and deterministic E2E/adversarial checks, creates an evidence/provenance anchor, and performs signature and mutation checks. `.github/workflows/cfr18.yml` runs the CFR-18 test and forensic exercise when its path filters or manual trigger apply.

A workflow file existing is not a passing workflow. For any verification claim, record the exact commit SHA, workflow run ID, conclusion, artifacts, and independent verification result. Historical baseline references in old evidence must not be presented as the status of current `main`.

## Running the prototype

The core AFE/LLM demo uses the Python standard library. Pinned root test tooling is declared in requirements-dev.txt; CFR-18 retains its own test and runtime dependencies.

Install the root development requirements before running the test suite:

~~~bash
python -m pip install -r requirements-dev.txt
~~~

Run from the repository root:

```bash
python run_e2e.py
python run_hybrid_e2e.py
python -m pytest -q
python tools/adversarial_matrix.py
```

CFR-18 has its own setup and instructions:

```bash
cd cfr18
cat README.md
make help
```

Check the current CFR-18 Makefile before using a target; some targets may require Docker and external tools.

## Configuration

The OpenAI-compatible provider reads:

- `LLM_BASE_URL` (defaults to `https://api.openai.com/v1`)
- `LLM_API_KEY`
- `LLM_MODEL` (defaults to `gpt-5` in the current source)

Never commit API keys. A deterministic provider is used by the checked-in E2E examples.

## Current classification

**PROTOTYPE / PARTIAL — NOT PRODUCTION-VERIFIED.**

The repository contains executable Python code, tests, CI definitions, and a CFR-18 exercise. Production readiness, real-world detection quality, real sandbox isolation, hosted-range tenant isolation, and live LLM behavior remain separate claims requiring independent runtime evidence.

## Repository

https://github.com/krzysztofcieciwa07-ship-it/vantage


## License status

No LICENSE file is currently present. The repository is visible on GitHub, but visibility does not grant a license to copy, modify, or redistribute the code. Choose and add an explicit license before describing this project as open source or granting external reuse rights.

## Repository governance

Engineering rules and contribution steps are maintained in docs/ENGINEERING_STANDARD.md and CONTRIBUTING.md. Security reporting guidance is in SECURITY.md. Use .github/PULL_REQUEST_TEMPLATE.md for source-SHA-bound verification records. Dependabot checks Python and GitHub Actions dependencies.
