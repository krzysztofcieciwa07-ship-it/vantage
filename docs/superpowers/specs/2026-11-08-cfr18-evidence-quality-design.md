# CFR-18 Evidence Quality — Design

**Date:** 2026-11-08  
**Scope:** Correct the CFR-18 laboratory scoring and evidence contract on the Vantage integration candidate.  
**Decision:** Keep the existing isolated Docker Compose scenario and its signed CI evidence anchor. Do not change the OLA production runtime or deploy anything.

## Intent

Make the CFR-18 result prove the contract it claims: a health-stability window derived from the generated incident, an independently supplied participant classification, a complete and truthful list of required artifacts, and no points awarded for fabricated operator activity.

## Findings being corrected

1. The run script always probes for 120 seconds although the incident manifest can require 100–140 seconds (seed 12345 requires 135 seconds). The scorer did not enforce the manifest's required window.
2. The harness created `self_report.json` from the same incident object later used to grade it. This made the answer self-fulfilling rather than an independent input.
3. The harness wrote a fixed command list to `bash_history.txt`; the scorer interpreted it as investigation quality. This was not an observed operator trace.
4. The incident generator still declared `self_report.json` and `bash_history.txt` as required evidence after those files were removed. That made the scenario's own evidence contract stale and inconsistent with the signed artifact.

## Chosen approach

Retain the current Docker Compose runtime and Evidence hash chain. Derive the probe duration from `incident.json`, record sub-second health samples through the entire required interval, and fail closed in both assertions and scoring if coverage is short, any sample is unhealthy, timestamps are unordered, or a gap exceeds two seconds.

Replace generated self-report with a separately supplied `participant_submission.json`. The local runner requires `CFR_PARTICIPANT_SUBMISSION`; CI passes an explicitly named reference fixture for its fixed seed. The scorer checks the report schema, non-empty root-cause text and evidence references, then compares the submitted fault classification with the incident. It does not claim to semantically validate the prose.

Remove synthetic shell history and the investigation-quality points derived from it. Automated CI reports `operator_trace_status=NOT_CAPTURED`; it does not award investigator-skill points.

Make `gen_incident.py` publish one canonical `required_evidence` list that names the actual final runtime artifacts. The assertions compare the generated list with the contract and verify that each listed file exists. External anchor and Sigstore files are governed separately by the manifest's external-anchor requirement.

## Non-goals

- No merge, deployment, OLA production change, or change to the Vantage policy service.
- No k3d migration, LLM-provider integration, or external network target.
- No claim that the CI reference fixture represents a real human investigation.
- No change to fault generation or Docker service topology.

## Verification

- Unit tests reject a 120-sample/119-second probe against a 135-second requirement, accept a full-duration healthy window with probes no more than two seconds apart, and reject failed health samples or sparse intervals.
- Unit tests reject missing/malformed participant submissions and distinguish correct from incorrect classifications.
- Unit tests pin the incident's required evidence list to the final artifact contract.
- GitHub Actions runs the Docker Compose forensic scenario, assertions, scoring, Evidence chain verification, Cosign signature verification, and signature-mutation rejection on the exact PR merge revision.
