# Vantage

Vantage is a deny-by-default execution gate prototype for routing tasks through detection, sandbox evaluation, incident stress, and a final decision gate.

## Pipeline

```
META-ORCHESTRATOR
        |
   AGENT SWARM
        |
   VANTAGE GATE
        |
     SANDBOX
        |
   INCIDENT LAB
        |
  DECISION GATE
        |
ALLOW / HUMAN_APPROVAL / BLOCK
```

## Evidence chain

The repository CI verifies:

1. exact commit checkout
2. automated tests
3. independent evidence verification
4. deterministic replay
5. replay determinism
6. provenance hash anchor
7. Sigstore/Cosign keyless signing
8. signature verification
9. mutation gate
10. artifact publication

A separate `workflow_run` workflow downloads the completed verification artifact and independently verifies its provenance, signature, commit binding, and evidence/replay hashes.

## Decision contract

- `ALLOW`: execution permitted
- `HUMAN_APPROVAL`: execution waits for explicit human approval
- `BLOCK`: execution denied

The current implementation is a prototype. Signature matching is heuristic and should not be treated as a complete security classifier.

## Verification status

Current verified baseline:

`3063bcd9268315910e9db4f72a3de1f875019831`

This status means the CI evidence chain passed for that exact revision. It does **not** claim that Vantage is production-ready or that the detector is comprehensive.

## Repository

GitHub: https://github.com/krzysztofcieciwa07-ship-it/vantage

## Security boundary (P0)

Vantage is a **policy prototype**, not an execution sandbox or a payment
authorization service. Its `ALLOW` verdict does not execute any side effects.
No source label is an identity proof: only `user_upload`, `public_web`, and
`anonymous_tool` are accepted as untrusted inputs at the same conservative
base risk. Unknown labels and privileged labels such as `verified_api` and
`known_partner` are blocked until a separate, independently verified source
attestation boundary exists.

Do not grant this component payment, transfer, bank, or production execution
permissions until an authenticated action-bound authorization boundary,
independent provenance verification, and real runtime tests have passed.
