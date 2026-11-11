## Summary

<!-- What changed and why? -->

## Scope and risk

- [ ] Detector or decision gate
- [ ] LLM provider / external network
- [ ] Evidence or provenance
- [ ] CFR-18 lab
- [ ] CI/CD or release process
- [ ] Documentation only

Describe the affected boundary and failure mode:

## Verification

| Check | Result | Exact run / evidence |
|---|---|---|
| Root pytest suite | NOT RUN | |
| Deterministic E2E / adversarial matrix | NOT RUN | |
| CFR-18 checks (if affected) | NOT RUN | |
| Provenance / mutation verification | NOT RUN | |

Candidate commit SHA:

## Safety review

- [ ] No credentials or private data included.
- [ ] Unknown states remain fail-closed.
- [ ] Test doubles and live providers are identified separately.
- [ ] Sandbox and detection limitations are stated accurately.
- [ ] No production-readiness claim is based only on CI configuration or mocked tests.

## Rollback

<!-- How can this change be safely reverted? -->
