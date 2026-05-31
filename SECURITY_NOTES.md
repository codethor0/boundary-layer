# Security Notes

## Security Assumptions

- Local lab components run on localhost or private Docker networks
- Production deployments require secrets from `.env.production` or a secrets manager
- `.env.example` values are non-production placeholders
- Mock LLM produces deterministic outputs; no real model behavior is represented
- HMAC secrets in examples must be rotated for any non-local use
- Redis lab keys use `boundary_layer:lab:redis:` namespace with TTLs

## Safe-Use Disclaimer

BoundaryLayer is for defensive education, secure engineering, and controlled local testing only. Do not use against systems you do not own or lack explicit permission to test.

## Local Lab Profile (`docker-compose.yml`)

- Authentication disabled by default for local education
- `/metrics` is unauthenticated for local Prometheus scraping
- Vulnerable lab modes are enabled
- Data store ports may be exposed on localhost for debugging

## Production Profile (`docker-compose.prod.yml`)

- API key authentication required on lab routes
- Metrics endpoint requires bearer token
- Vulnerable lab modes disabled
- Rate limiting uses Redis-backed distributed counters in production
- Redis and PostgreSQL are internal-only (no host ports)
- TLS termination at Nginx on port 8443 (bound to localhost by default)
- Alert webhook requires bearer token
- OpenAPI/docs endpoints disabled in production
- `/ready` requires metrics bearer token; dependency details are sanitized
- Prometheus and Alertmanager UIs are internal-only (not proxied through nginx)
- Application containers run as non-root with read-only root filesystems
- CI runs `make validate-prod` on main via `.github/workflows/prod-validate.yml`

See [docs/PRODUCTION.md](docs/PRODUCTION.md) for deployment steps.

## Known Limitations

- Vulnerable modes intentionally demonstrate insecure behavior (local lab only)
- Labs simulate infrastructure risks; they do not reproduce confirmed production exploits
- Mock LLM is deterministic and not representative of real model behavior
- Write storm lab uses bounded synthetic inserts; does not simulate production WAL or disk exhaustion
- Circuit breaker lab uses synthetic work units; does not generate real inference load
- SSE exhaustion lab uses synthetic stream units; does not open real long-running streams
- Prompt cache lab uses synthetic prompt prefixes only; does not store real prompts
- File upload lab uses synthetic metadata only; does not parse real files or run external parsers
- BoundaryLayer is not a WAF replacement or managed security product

## Local-Only Testing Warning

Keep local lab Docker ports bound to localhost. Do not expose the local lab stack to untrusted networks. Do not commit `.env`, real credentials, or unsanitized attack transcripts.

## Metrics Exposure

The `/metrics` endpoint exposes lab counter values. Local lab mode leaves metrics open for Prometheus scraping. Production mode requires bearer token authentication.
