# Vantage → OLA: signed, operation-scoped decision contract (pilot)

**Stage:** review candidate only, not an approved production trust boundary. The detector remains heuristic.

## Endpoint and required identity

- `POST /v1/decisions` is served by the **actual** Vantage `AFE` pipeline in `afe_vantage.py`.
- Caller authentication: HMAC-SHA256, secret at least 32 bytes, across canonical JSON body, Unix timestamp and 128-bit nonce. Headers: `X-OLA-Timestamp`, `X-OLA-Nonce`, `X-OLA-Signature`.
- Clock skew 30 s maximum; each nonce is committed to persistent SQLite with uniqueness. Missing/invalid authentication → `401`; reused nonce → `409`; unavailable persistence → `503`.
- Request: `{schema:"ola.vantage.request.v1", operation_id, tenant_id, action, task_sha256, task_text}`. UUID values must be canonical; `task_text` is bounded and must hash to `task_sha256`.
- The service fixes `source="user_upload"` and `task_type="security"`; callers may NOT lower the risk by claiming a privileged input source.
- **Only `action="safe_expression"` can produce ALLOW**. Unknown or privileged actions return a signed BLOCK. An AFE `HUMAN_APPROVAL` response is **not** ALLOW.

## Decision signature

The service creates a canonical JSON receipt and signs **its exact UTF-8 bytes** using Ed25519. The response is `{receipt:{...},signature:<base64-ed25519-64-byte>}`.

The signed receipt binds: `operation_id`, `tenant_id`, `action`, `task_sha256`, verdict, score components, classifier (`vantage.AFE`), source commit, issued and expiry time (at most 30 s), request nonce and public-key identifier. It explicitly sets `trust_scope="signed_heuristic_policy_only"` and `production_authorized=false`.

OLA must independently verify the signature with a **trusted, pinned public key** and check each field against the exact request. A signed ALLOW is valid for **one bounded local preflight**; it cannot authorize deploying, shell, Codex, NOVA, payment or other privileged effects.

## Startup and key custody

Use cryptography 50.0.2 or a reviewed newer pin and provision per-environment private keys outside git. Supply:

- `VANTAGE_ED25519_PRIVATE_KEY_FILE` – PEM file only readable by the service user (0600, no symlink).
- `VANTAGE_HMAC_SECRET` – 32+ random bytes represented as a private environment secret; do not print or commit.
- `VANTAGE_SOURCE_COMMIT` – verified exact 40-hex SHA of the deployed Vantage source.
- `VANTAGE_REPLAY_DB` – writable SQLite file on a persistent private volume.
- `VANTAGE_BIND_HOST=127.0.0.1` by default, `VANTAGE_PORT=18710` by default.

For a Docker **private network only**, set `VANTAGE_BIND_HOST=0.0.0.0` with explicit `VANTAGE_PRIVATE_NETWORK_BIND=1` and DO NOT publish its port; use authenticated TLS/mTLS gateway for host-to-host production connections.

No private key, HMAC token or unencrypted business task should be uploaded to CI artifacts. Rotate keys through a controlled dual-public-key transition, never by silently overwriting trusted keys.

## Open release gates

1. Cross-repository HTTP integration between real OLA and real Vantage containers at a tested source SHA.
2. Negative mutation tests for source, request body, tenant, operation ID, signature, expiration, and failure of nonce storage.
3. Independent review, accepted branch protection, signed source-to-image provenance, sustained health and recovery.
4. Production TLS/mTLS, replay database durability across restarts and backups, secret rotation, rate limiting, monitoring and source-attestation.
5. Same `operation_id` correlation with Codex Bridge and NOVA **without** treating those services as trusted until their own authenticated contracts are tested.

Default system verdict: **BLOCKED / NOT_PRODUCTION_AUTHORIZED**.
