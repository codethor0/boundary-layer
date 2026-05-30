# Security Notes

## Security Assumptions

- All components run on localhost or private Docker networks
- `.env.example` values are non-production placeholders
- Mock LLM produces deterministic outputs; no real model behavior is represented
- HMAC secrets in examples must be rotated for any non-local use
- Redis lab keys use `boundary_layer:lab:redis:` namespace with TTLs

## Safe-Use Disclaimer

BoundaryLayer is for defensive education, secure engineering, and controlled local testing only. Do not use against systems you do not own or lack explicit permission to test.

## Known Limitations

- Vulnerable modes intentionally demonstrate insecure behavior
- No authentication on API endpoints (local lab only)
- `/metrics` is unauthenticated for local Prometheus scraping
- Prometheus Alertmanager routes to placeholder localhost URLs
- No TLS between Compose services
- Live Redis mode writes ephemeral lab keys only; not production session patterns
- Write storm lab uses bounded synthetic inserts; does not simulate production WAL or disk exhaustion
- Circuit breaker lab uses synthetic work units; does not generate real inference load
- SSE exhaustion lab uses synthetic stream units; does not open real long-running streams
- Prompt cache lab uses synthetic prompt prefixes only; does not store real prompts
- Prompt cache lab is a preventive architecture simulation, not a confirmed exploit reproduction
- File upload lab uses synthetic metadata only; does not parse real files or run external parsers
- Alertmanager routes alerts only to the local in-memory webhook on port 8081
- No PagerDuty, Slack, email, or other external alert integrations are configured

## Local-Only Testing Warning

Keep Docker ports bound to localhost. Do not expose the stack to untrusted networks. Do not commit `.env`, real credentials, or unsanitized attack transcripts.

## Metrics Exposure

The `/metrics` endpoint exposes lab counter values. Acceptable for local labs only. Do not expose publicly without authentication and network controls.
