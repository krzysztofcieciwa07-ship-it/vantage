# Security Policy

## Scope and project status

This policy covers the Vantage prototype, its root verification tooling, LLM provider wrappers, and the CFR-18 exercise in this repository.

The project is classified as PROTOTYPE / PARTIAL — NOT PRODUCTION-VERIFIED. No production security service level, incident response time, or security certification is implied.

## Reporting a vulnerability

Use GitHub private vulnerability reporting for this repository when that feature is enabled. If it is unavailable, contact the repository maintainer directly through GitHub. Do not publish credentials, customer data, or an actionable exploit in a public issue.

Include the affected commit, impact, minimal sanitized reproduction, and any relevant workflow run. Do not include API keys or other secrets.

## Security invariants

- Unknown, malformed, or unverifiable conditions must not be promoted to ALLOW or VERIFIED.
- A deterministic hash-derived score is not a process or code-execution sandbox.
- Pattern matching is not a complete prompt-injection or malicious-instruction detector.
- Agreement between model providers is not proof of factual correctness or independent verification.
- Fallback to a deterministic provider must be visible and must not be reported as a successful primary-provider call.
- CI success proves only the checks actually executed on the identified source SHA.

## Credentials and external services

Store provider keys in local environment variables or an approved secret manager. Never commit .env files or print secrets to logs. Use explicit timeouts and restrict outbound destinations when adding network integrations.

## Release and remediation evidence

For security-related changes, retain the exact source SHA, workflow run, relevant test and mutation results, artifact digests, and independent verification outcome. Record unavailable controls as UNKNOWN. A workflow definition or a passing deterministic test does not establish production safety.
