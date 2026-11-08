# CFR-18 Evidence Quality Implementation Plan

> **For agentic workers:** Execute this plan task-by-task with the current GitHub branch as the isolated workspace. Steps use checkbox syntax for tracking.

**Goal:** Make CFR-18 enforce the manifest-defined health-stability interval, grade a separately supplied participant submission, and stop awarding points for fabricated command history.

**Architecture:** Preserve the existing Compose scenario, append-only Evidence chain and Cosign anchor. Add pure scoring validators, make the run script consume the generated incident window and an external submission file, then update assertions and CI artifact inputs.

**Tech Stack:** Python 3.12, pytest, POSIX shell, Docker Compose, GitHub Actions, Cosign.

**Spec:** `docs/superpowers/specs/2026-11-08-cfr18-evidence-quality-design.md`

## Global Constraints

- No merge, deployment, production changes, or external network targets.
- Run against the exact source SHA; keep the PR Draft.
- Missing or invalid participant input and incomplete health windows fail closed.
- CI's fixed-seed reference submission is explicitly a test fixture, not evidence of human performance.
- No fabricated shell history or investigator-quality points.

## Review Focus

- 120 probes against a 135-second requirement must fail.
- A passing health sample count with any unhealthy sample must fail.
- Missing timestamps, duplicate/non-monotonic timestamps, and malformed ISO-8601 values must fail.
- Missing, malformed, empty, or wrong-schema participant reports must not receive a passing result.
- A valid but incorrect fault classification must be graded incorrect rather than treated as missing.
- Re-running the scenario must not overwrite a participant submission source file or include fake operator traces.

---

### Task 1: Pin the quality contracts with failing tests

**Files:**
- Modify: `cfr18/tests/test_cfr18.py`
- Create: `cfr18/tests/test_cfr18_quality.py`

**Interfaces:**
- Consumes: existing `ci.score` module and existing deterministic timestamp/incident contracts.
- Produces: tests requiring `evaluate_probe_window(probes, required_window_s)` and `validate_participant_submission(incident, submission)`.

- [ ] Add tests for 120 samples spanning 119 seconds failing a 135-second requirement; 136 healthy samples spanning 135 seconds passing; and any failed health probe invalidating the window.
- [ ] Add tests for missing/malformed submissions and a separately supplied valid report with correct vs incorrect fault type.
- [ ] Run `pytest -q` in `cfr18` through the PR workflow and record the expected RED failure because the new behavior is not implemented.
- [ ] Commit the tests and open a Draft follow-up PR targeting the signed Vantage/CFR-18 integration branch.

### Task 2: Enforce the contract in runtime, scoring and CI

**Files:**
- Modify: `cfr18/ci/score.py`
- Modify: `cfr18/scripts/live_forensic.sh`
- Modify: `cfr18/scripts/probe.sh`
- Modify: `cfr18/ci/assertions.sh`
- Modify: `.github/workflows/cfr18.yml`
- Modify: `cfr18/README.md`
- Create: `cfr18/tests/fixtures/participant_submission_seed_12345.json`

**Interfaces:**
- Consumes: incident `hidden_required_window_s`; external file named by `CFR_PARTICIPANT_SUBMISSION`.
- Produces: Evidence `participant_submission.json`; score schema `CFR-18/forensic-score-v3`; probe-window metrics `required_window_s`, `observed_window_s`, `sample_count`, and `passed`.

- [ ] Implement `evaluate_probe_window` and `validate_participant_submission` to satisfy the RED tests.
- [ ] Make `live_forensic.sh` require and copy the participant report; remove generated `self_report.json` and template `bash_history.txt`.
- [ ] Derive `DURATION` from the generated incident and collect samples until the elapsed interval is at least the required duration.
- [ ] Make assertions and scoring independently reject short, unhealthy or malformed windows and invalid participant input.
- [ ] Remove investigation-quality points derived from synthetic command text; report `operator_trace_status=NOT_CAPTURED`.
- [ ] Update Evidence snapshots, signed-anchor file list, artifact bundle and local run instructions.
- [ ] Run focused tests, full pytest, Docker Compose live forensic test, assertions, score, Evidence-chain verification, Cosign verification and signature mutation rejection on the new exact SHA.
- [ ] Keep both the existing integration PR and the follow-up PR unmerged and Draft pending independent review.
