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

## Development Stack Is Not Hardened

The default `docker-compose.yml` dev stack (`make up`) is for **local learning only**:

- Lab endpoints, `/metrics`, and the alert webhook are **unauthenticated** by default
- PostgreSQL, Redis, mock LLM, Prometheus, and Alertmanager bind to **localhost ports**
- Credentials in `docker-compose.yml` are **placeholder lab secrets**, not production values
- **Do not** deploy `docker-compose.yml` to public infrastructure or multi-tenant environments

Use `docker-compose.prod.yml` only on machines you control, with secrets from `.env.production` and the guidance in [docs/PRODUCTION.md](docs/PRODUCTION.md). Even the production-like profile is a **local validation profile**, not a complete SaaS hardening program.

## Rate Limiting and Proxy Headers

- **Development:** Redis-backed rate limiting (when enabled) **fails open** if Redis is unavailable. This preserves local lab availability and is logged.
- **Production-like profile:** Redis-backed rate limiting **fails closed** with HTTP 503 when Redis is unavailable.
- **X-Forwarded-For:** Ignored by default. The production-like profile sets `BOUNDARY_LAYER_TRUST_PROXY_HEADERS=true` and uses the **rightmost** X-Forwarded-For hop (as appended by nginx). Do not expose the API directly without nginx when proxy headers are trusted.

## Known Limitations

- Mock LLM is deterministic, not representative of all model behaviors
- Alert webhook stores alerts in memory only
- HMAC secrets in `.env.example` are placeholders for local dev only
- Labs simulate scenarios; they do not guarantee coverage of all attack variants
- Default CI runs unit tests, lint, security scan, and production validate workflows; full local Docker gate remains `make validate` / `make validate-e2e`

## Dependencies

Review `apps/api/requirements.txt` and run validation secret scans before sharing local bundles.

## Repository Hygiene

Prompt artifacts, agent transcripts, editor tooling files, and generated validation reports must not be committed to the public repository. Local release bundles may include validation output for review purposes only.
