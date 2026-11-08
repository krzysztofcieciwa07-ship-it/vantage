# CFR-18 Evidence Quality Implementation Plan

> **For agentic workers:** Execute this plan task-by-task with the current GitHub branch as the isolated workspace. Steps use checkbox syntax for tracking.

**Goal:** Make CFR-18 enforce the manifest-defined health-stability interval, grade a separately supplied participant submission, ensure the incident requires actual artifacts, and keep score calculations accurate at the exact threshold.

**Architecture:** Preserve the existing Compose scenario, append-only Evidence chain and Cosign anchor. Add pure scoring validators, make the run script consume the generated incident window and an external submission file, align the incident's required-evidence list, and report sampled health separately from end-to-end availability.

**Tech Stack:** Python 3.12, pytest, POSIX shell, Docker Compose, GitHub Actions, Cosign.

**Spec:** `docs/superpowers/specs/2026-11-08-cfr18-evidence-quality-design.md`

## Global Constraints

- No merge, deployment, production changes, or external network targets.
- Run against the exact source SHA; keep the PR Draft.
- Missing or invalid participant input and incomplete health windows fail closed.
- CI's fixed-seed reference submission is explicitly a test fixture, not evidence of human performance; it receives no diagnosis bonus.
- No fabricated shell history or investigator-quality points.
- The incident's required runtime evidence list must match the final runtime artifacts exactly.
- Post-recovery probe success must not be called whole-incident availability; MTTR stays NOT_CAPTURED without event timestamps.
- Threshold comparisons use full precision; display rounding must not affect pass/fail.

## Review Focus

- 120 probes spanning only 119 seconds against a 135-second requirement must fail.
- A 134.9996-second window must fail even though its displayed rounded duration is 135.000 seconds.
- A 2.0004-second probe gap must fail even though its displayed rounded gap is 2.000 seconds.
- A full-duration window with any unhealthy sample must fail.
- A full-duration window with a gap longer than two seconds must fail.
- Probe success ratio must measure only the supplied probes and return 0 for an empty set.
- The CI reference fixture must not receive a diagnosis bonus; participant-source submissions remain separately graded.
- Missing timestamps, duplicate/non-monotonic timestamps, and malformed ISO-8601 values must fail.
- Missing, malformed, empty, or wrong-schema participant reports must not receive a passing result.
- A valid but incorrect fault classification must be graded incorrect rather than treated as missing.
- The incident must not declare removed files as required evidence, and every required path must exist by assertion time.
- Re-running the scenario must not overwrite a participant submission source file or include fake operator traces.

---

### Task 1: Pin the quality contracts with failing tests

**Files:**
- Modify: `cfr18/tests/test_cfr18.py`
- Create: `cfr18/tests/test_cfr18_quality.py`

**Interfaces:**
- Consumes: existing `ci.score` module and deterministic timestamp/incident contracts.
- Produces: tests requiring `evaluate_probe_window(probes, required_window_s)`, `validate_participant_submission(incident, submission)`, `probe_success_ratio(probes)`, `participant_scoring_adjustment(submission, submission_check)`, and `build_incident(seed, opened_at)`.

- [ ] Test exact window boundaries and full-precision max-gap comparisons.
- [ ] Test that CI fixture answers receive no diagnosis bonus and participant classifications are scored separately.
- [ ] Test that probe success ratio reflects only the supplied health probes and returns zero for an empty set.
- [ ] Test missing/malformed submissions and a separately supplied valid report with correct vs incorrect fault type.
- [ ] Test that `build_incident` declares exactly the actual runtime artifacts: chain, incident, manifest, probes, participant submission, score, runtime events, and processed jobs.
- [ ] Run `pytest -q` in `cfr18` through the PR workflow and record expected RED failures before implementation.

### Task 2: Enforce the contract in runtime, scoring and CI

**Files:**
- Modify: `cfr18/ci/gen_incident.py`
- Modify: `cfr18/ci/score.py`
- Modify: `cfr18/scripts/live_forensic.sh`
- Modify: `cfr18/scripts/probe.sh`
- Modify: `cfr18/ci/assertions.sh`
- Modify: `.github/workflows/cfr18.yml`
- Modify: `cfr18/README.md`
- Create: `cfr18/tests/fixtures/participant_submission_seed_12345.json`

**Interfaces:**
- Consumes: incident `hidden_required_window_s`; external file named by `CFR_PARTICIPANT_SUBMISSION`.
- Produces: Evidence `participant_submission.json`; score schema `CFR-18/forensic-score-v3`; probe-window metrics `required_window_s`, `observed_window_s`, `max_gap_s`, `sample_count`, and `passed`; score metrics `probe_success_ratio`, `mttr_status=NOT_CAPTURED`, and `participant_classification_status`.

- [ ] Implement the failing unit contracts.
- [ ] Make `live_forensic.sh` require and copy the participant report; remove generated `self_report.json` and template `bash_history.txt`.
- [ ] Derive probe duration from the generated incident and stop only after the first-to-last timestamp interval reaches the required duration.
- [ ] Make assertions and scoring independently reject short, unhealthy, unordered, malformed, or sparse windows and invalid participant input.
- [ ] Compare raw duration and gap values before rounding metrics for display.
- [ ] Remove investigation-quality points derived from synthetic command text; report `operator_trace_status=NOT_CAPTURED`.
- [ ] Give `CI_REFERENCE_FIXTURE` no participant diagnosis adjustment.
- [ ] Generate one canonical required-evidence list and assert that each declared runtime artifact exists; remove stale self-report/history entries.
- [ ] Report post-recovery probe success separately; leave whole-incident availability and MTTR unmeasured until event timestamps are available.
- [ ] Update Evidence snapshots, signed-anchor file list, artifact bundle and local run instructions.
- [ ] Run focused tests, full pytest, Docker Compose live forensic test, assertions, score, Evidence-chain verification, Cosign verification and signature mutation rejection on the new exact SHA.
- [ ] Keep the integration PR and follow-up PR unmerged and Draft pending independent review.
