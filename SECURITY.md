# Security Policy

## Supported Scope

BoundaryLayer is intended for **local educational and defensive engineering use only**. It is not a production security product.

## Reporting Vulnerabilities

If you find a security issue in BoundaryLayer itself, open a private disclosure via [GitHub Security Advisories](https://github.com/codethor0/boundary-layer/security/advisories) or contact maintainers directly. Do not exploit vulnerabilities outside your local lab environment.

## Safe Use

- Run only on systems you control
- Do not point labs at production infrastructure
- Do not commit secrets, API keys, or unsanitized attack transcripts
- Use `.env.example` as template; keep `.env` local
- Do not commit generated validation reports or build transcripts to Git

## Known Limitations

- Mock LLM is deterministic, not representative of all model behaviors
- Alert webhook stores alerts in memory only
- HMAC secrets in `.env.example` are placeholders for local dev only
- Labs simulate scenarios; they do not guarantee coverage of all attack variants
- Default CI does not run full Docker Compose validation; use local `make validate`

## Dependencies

Review `apps/api/requirements.txt` and run validation secret scans before sharing local bundles.

## Repository Hygiene

Prompt artifacts, agent transcripts, editor tooling files, and generated validation reports must not be committed to the public repository. Local release bundles may include validation output for review purposes only.
