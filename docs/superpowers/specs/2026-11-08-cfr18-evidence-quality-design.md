# CFR-18 Evidence Quality — Design

**Date:** 2026-11-08  
**Scope:** Correct the CFR-18 laboratory scoring and evidence contract on the Vantage integration candidate.  
**Decision:** Keep the existing isolated Docker Compose scenario and its signed CI evidence anchor. Do not change the OLA production runtime or deploy anything.

## Intent

Make the CFR-18 result prove the contract it claims: a health-stability window derived from the generated incident, an independently supplied participant classification, a complete and truthful list of required artifacts, honest metric names, precise boundary checks, and no points awarded for fabricated operator activity, a CI answer fixture, or nonexistent evidence.

## Findings being corrected

1. The run script always probed for 120 seconds although the incident manifest can require 100–140 seconds (seed 12345 requires 135 seconds). The scorer did not enforce the manifest's required window.
2. The harness created `self_report.json` from the same incident object later used to grade it. This made the answer self-fulfilling rather than an independent input.
3. The harness wrote a fixed command list to `bash_history.txt`; the scorer interpreted it as investigation quality. This was not an observed operator trace.
4. The incident generator still declared `self_report.json` and `bash_history.txt` as required evidence after those files were removed. That made the scenario's own evidence contract stale and inconsistent with the signed artifact.
5. The score called post-recovery health probes `availability`, although those probes do not measure service availability across the fault and recovery interval. Runtime events also lack timestamps, so MTTR cannot be calculated.
6. The checked-in `CI_REFERENCE_FIXTURE` was structurally separate but still received the positive participant-diagnosis scoring adjustment. A deterministic CI fixture is not a participant performance record.
7. Probe window and max-gap values were rounded before threshold comparisons. Values just outside the contract (134.9996 s and 2.0004 s) could round to passing display values.
8. Participant reports accepted any non-empty source label, and evidence references were not resolved against actual JSONL records. This allowed arbitrary source claims and nonexistent evidence pointers.

## Chosen approach

Retain the current Docker Compose runtime and Evidence hash chain. Derive the probe duration from `incident.json`, record sub-second health samples through the entire required interval, and fail closed in both assertions and scoring if coverage is short, any sample is unhealthy, timestamps are unordered, or a gap exceeds two seconds. Compare raw timestamp values at full precision; round only the emitted display metrics.

Replace generated self-report with a separately supplied `participant_submission.json`. The local runner requires `CFR_PARTICIPANT_SUBMISSION`; CI passes an explicitly named reference fixture for its fixed seed. The only accepted source labels are `participant` and `CI_REFERENCE_FIXTURE`. Every evidence reference must match `relative/path.jsonl#field=value`, point to a file in a small allow-list of declared runtime JSONL evidence, and resolve to at least one real record. Path traversal and non-declared files are rejected. The scorer checks the report schema, source label, non-empty root-cause text and resolved evidence references, then compares the submitted fault classification with the incident. It does not claim to semantically validate the prose or authenticate the submitting person.

Remove synthetic shell history and the investigation-quality points derived from it. Automated CI reports `operator_trace_status=NOT_CAPTURED`; it does not award investigator-skill points.

Make `gen_incident.py` publish one canonical `required_evidence` list that names the actual final runtime artifacts. The assertions compare the generated list with the contract and verify that each listed file exists. External anchor and Sigstore files are governed separately by the manifest's external-anchor requirement.

Call the health metric `probe_success_ratio` and document that it covers only the post-recovery stability window. Emit `mttr_status=NOT_CAPTURED` until runtime event timestamps and an explicit recovery-time definition are added. The exact `CI_REFERENCE_FIXTURE` receives no participant diagnosis adjustment; scoring adjustments are reserved for explicitly labelled participant submissions.

## Non-goals

- No merge, deployment, OLA production change, or change to the Vantage policy service.
- No k3d migration, LLM-provider integration, or external network target.
- No claim that the CI reference fixture represents a human investigation.
- No claim of whole-incident service availability or MTTR from the current evidence set.
- No identity authentication for participant submissions in this phase.
- No change to fault generation or Docker service topology.

## Verification

- Unit tests reject a 120-sample/119-second probe against a 135-second requirement, accept a full-duration healthy window with probes no more than two seconds apart, and reject failed health samples or sparse intervals.
- Unit tests prove that a 134.9996-second window and a 2.0004-second maximum gap do not pass by rounding to the threshold.
- Unit tests verify that probe success ratio describes only the sampled probe set and returns zero for an empty set.
- Unit tests verify that the CI reference fixture receives no diagnosis bonus, while an explicit participant classification is separately adjusted.
- Unit tests reject missing/malformed participant submissions, unknown source labels, path traversal, unresolved selectors, and nonexistent evidence files.
- Unit tests distinguish correct from incorrect classifications and pin the incident's required evidence list to the final artifact contract.
- GitHub Actions runs the Docker Compose forensic scenario, assertions, scoring, Evidence chain verification, Cosign signature verification, and signature-mutation rejection on the exact PR merge revision.
