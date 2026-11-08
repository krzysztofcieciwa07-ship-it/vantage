# CFR-18 Evidence Quality — Design

**Date:** 2026-11-08  
**Scope:** Correct the CFR-18 laboratory scoring and evidence contract on the Vantage integration candidate.  
**Decision:** Keep the existing isolated Docker Compose scenario and its signed CI evidence anchor. Do not change the OLA production runtime or deploy anything.

## Intent

Make the CFR-18 result prove the contract it claims: a health-stability window derived from the generated incident, an independently supplied participant classification, and no points awarded for fabricated operator activity.

## Findings being corrected

1. The run script always probes for 120 seconds although the incident manifest can require 100–140 seconds (seed 12345 requires 135 seconds). The scorer currently does not check the manifest's required window.
2. The harness creates `self_report.json` from the same incident object later used to grade it. This makes the answer self-fulfilling rather than an independent input.
3. The harness writes a fixed command list to `bash_history.txt`; the scorer interprets it as investigation quality. This is not an observed operator trace.

## Chosen approach

Retain the current Docker Compose runtime and Evidence hash chain. Derive the probe duration from `incident.json`, record enough health samples to cover the entire elapsed window, and fail closed in both assertions and scoring if the samples are short, unhealthy, unordered, or malformed.

Replace generated self-report with a separately supplied `participant_submission.json`. The local runner requires `CFR_PARTICIPANT_SUBMISSION`; CI passes an explicitly named reference fixture for its fixed seed. The scorer checks the report schema, non-empty root-cause text and evidence references, then compares the submitted fault classification with the incident. It does not claim to semantically validate the prose.

Remove synthetic shell history and the investigation-quality points derived from it. Automated CI reports `operator_trace_status=NOT_CAPTURED`; it does not award investigator-skill points. A future interactive participant runner can provide an independently captured and signed operator trace.

## Non-goals

- No merge, deployment, OLA production change, or change to the Vantage policy service.
- No k3d migration, LLM-provider integration, or external network target.
- No claim that the CI reference fixture represents a real human investigation.
- No change to fault generation or Docker service topology.

## Verification

- Unit tests reject a 120-sample/119-second probe against a 135-second requirement, accept a complete 135-second healthy window, and reject failed health samples.
- Unit tests reject missing/malformed participant submissions and distinguish correct from incorrect classifications.
- GitHub Actions runs the Docker Compose forensic scenario, assertions, scoring, Evidence chain verification, Cosign signature verification, and signature-mutation rejection on the exact PR SHA.
