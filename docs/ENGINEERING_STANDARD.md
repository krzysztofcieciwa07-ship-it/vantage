# Repository Engineering Standard

This document defines the minimum engineering and evidence standard for this repository. It is a working standard, not a security certification.

## Source of truth

- Executable source and tests define implemented behavior.
- Configuration and workflow files define how checks are run; they are not proof that a check passed.
- README and docs must describe observed implementation, not an aspirational roadmap.
- When documentation conflicts with code or a current run, record the discrepancy and verify the source commit before changing either.

## Required change quality

1. Keep changes focused and reviewable.
2. Preserve explicit module boundaries and typed request/response contracts.
3. Validate untrusted input at boundaries and fail closed on malformed, missing, or unverifiable data.
4. Apply explicit limits to input size, nesting/depth, execution time, retries, and outbound network destinations where relevant.
5. Keep secrets out of source, logs, artifacts, examples, and issue reports.
6. Add regression tests for fixed defects. Add integration or adversarial tests when trust boundaries change.
7. Document operational configuration, migration steps, health checks, and rollback behavior when they change.

## Verification vocabulary

Use these terms consistently:

- PASS — the named check completed successfully on the exact candidate SHA.
- FAIL — the check ran and found a failure.
- PARTIAL — only some required checks or scenarios passed.
- BLOCKED — a required check could not proceed because a prerequisite failed or was unavailable.
- UNKNOWN — no adequate evidence exists.

A skipped check is not a pass. A test double is not a live provider. A local hash is not proof of source identity. Provider agreement is not proof of factual correctness. A green workflow is not evidence of production readiness unless it covers the required runtime boundary.

## CI and supply chain

- Workflows must check out and verify the intended source SHA.
- Grant the minimum GITHUB_TOKEN permissions required by each job.
- Pin third-party Actions to immutable full commit SHAs and annotate the reviewed version.
- Keep test dependencies reproducible and reviewed.
- Preserve test, security, provenance, and release artifacts with their source commit and workflow run identifiers.
- Avoid adding overlapping workflows until existing triggers and coverage have been mapped.
- Treat `workflow_run` as a separate trust boundary: GitHub evaluates that workflow from the default branch, while the signer identity belongs to the triggering run. Derive the expected identity from the triggering event (`pull_request` number or source branch), reject missing context, and verify both PR and branch-triggered paths.

## Release evidence

A release decision should identify, as applicable:

1. repository and exact source commit;
2. workflow run IDs and conclusions;
3. unit, integration, adversarial, and mutation results;
4. artifact digests and verifiable provenance;
5. real provider/runtime health and stability window;
6. isolation, migration, rollback, and human-authorization evidence.

Do not infer production readiness from a green badge, a merged pull request, a workflow file, deterministic provider tests, or hash-derived synthetic metrics.

## Review expectations

Every pull request must describe scope, risks, checks actually run, unresolved findings, and rollback. Changes to the decision gate, external provider calls, evidence integrity, or execution boundary require explicit review of those boundaries.
