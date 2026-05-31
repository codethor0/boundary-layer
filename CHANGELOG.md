# Changelog

All notable changes to BoundaryLayer are documented here.

## v1.3.4 (2026-05-31)

- Align release tag with 10/10 polish docs and commands (`make smoke`, `make demo`, `make validate-alerts`)
- Add fresh-volume PostgreSQL restore validation (`make validate-restore-fresh-volume`)
- Add sanitized demo transcript capture (`make capture-demo`, `docs/assets/demo-transcript.txt`)
- Metrics catalog, observability walkthrough, troubleshooting, ADD_A_LAB, and live-vs-simulated docs from polish pass
- Authz alert delivery validated in `make validate` alongside circuit breaker alert
- Release title pattern: local lab polish and validation (not hosted SaaS readiness)

### v1.3.4 gap closure (post-tag)

- Fix restore seed field: `requested_writes: 25` (was ignored `event_count`)
- Extend `make validate-alerts` to six deterministic alerts (circuit breaker, authz, redis tamper, write storm, SSE backpressure, prompt deletion)
- Clarify SSE hardened `blocked` semantics in docs, validate gate, and tests
- Add explicit restore volume reset warnings in README, BACKUP_RESTORE, TROUBLESHOOTING, and Makefile help
- Assert exact `write_storm_events=25` in fresh-volume restore validation

Known limitations (unchanged):

- Local defensive security lab only; not a hosted production SaaS
- Dev stack is intentionally unauthenticated
- Alert webhook storage is in-memory only
- Fresh-volume restore validates local Compose Postgres only, not off-host DR
- Terminal GIF may require optional asciinema/agg tooling; transcript is the default artifact

## v1.3.3 (2026-05-31)

- Production readiness audit fixes: restore roundtrip, API restart/recovery validation, validation curl noise reduction
- Fix Production Validate CI Redis health (TLS key permissions for non-root Redis on Linux runners)
- Fix Security Scan CI: repo-level Hadolint DL3008 ignore, Trivy pinned to immutable release with library-only scan policy
- Harden rate limiting: fail-closed in production-like profile when Redis limiter is unavailable; safe X-Forwarded-For handling
- Document dev stack insecurity and mock LLM integration scope
- Live validation pass: local clean-room gates, production-like profile, bundle hygiene verified
- GitHub Actions green on CI, Security Scan, and Production Validate at release commit

Known limitations (unchanged):

- Local defensive security lab only; not a hosted production SaaS
- Dev stack is intentionally unauthenticated
- Alert webhook storage is in-memory only
- Restore validation is table-scoped unless improved
- Trivy policy excludes unfixed base-image OS CVEs from blocking CI

## v1.3.2

- Upgrade FastAPI to 0.136.3 to resolve Starlette CVEs flagged by pip-audit
- Extend production validation with rate-limit (429) and webhook storage cap (413) checks
- Add `scripts/bug-hunt-prod.sh` for standalone production adversarial QA

## v1.3.1

- Fix nginx rate limiting to return HTTP 429 instead of misleading 503 responses
- Harden Redis rate limiter against transient Redis failures during checks
- Cap alert webhook in-memory storage with configurable maximum and HTTP 413 responses
- Restrict TrustedHost middleware to production and isolate unit tests from exported prod env vars

## v1.3.0

- Add internal Postgres/Redis TLS, ingress cert rotation tooling, and TLS runbook
- Add secrets manager examples (Vault, AWS SM), backup/restore scripts, and runbooks
- Add Hadolint, pip-audit, and Trivy security scanning in CI
- Add `make validate-e2e` for full local + production end-to-end validation gate

## v1.2.0

- Harden production containers with non-root users, read-only root filesystems, and resource limits
- Replace in-memory rate limiting with Redis-backed distributed limiter in production
- Lock down production surface area: authenticated `/ready`, disabled OpenAPI, no public Prometheus/Alertmanager via nginx
- Restrict uvicorn forwarded-allow-ips, strengthen nginx TLS settings, bind ingress to localhost by default
- Validate production data-store secret strength at startup and add CI `validate-prod` workflow

## v1.1.0

- Added production deployment profile with API authentication, metrics protection, and rate limiting
- Added TLS ingress via Nginx, Alembic migrations, structured JSON logging, and production Compose stack
- Added authenticated alert webhook receiver and Slack/PagerDuty Alertmanager templates
- Added Redis password support for secured production Redis deployments
- Local lab mode (`docker-compose.yml`) remains backward compatible with auth disabled by default

- Added `/ready` dependency health endpoint and `make validate-prod` production gate
- Added alert webhook authentication tests and production stack validation script

## v1.0.10

- Redesigned logo with Strata Conduit concept: layered infrastructure strata and vertical inspection conduit
- Updated logo concepts, production SVG assets, and visual identity documentation
- Re-ran exploratory testing and full validation across the Docker stack
- Confirmed generated reports, build transcripts, and prompt artifacts remain excluded from Git

## v1.0.9

- Added deeper QA documentation for API contracts, invalid inputs, metrics, live Redis, live PostgreSQL, Prometheus, Alertmanager, and restart testing
- Re-ran deeper end-to-end bug-hunting validation across the full Docker stack
- Confirmed all nine labs behave as documented in vulnerable and hardened modes
- Confirmed invalid inputs fail closed
- Confirmed generated reports, build transcripts, and prompt artifacts remain excluded from Git
- Fixed bundle verification false positive that rejected `.env.example` as a tracked `.env` file

## v1.0.8

- Added final live Docker release-gate documentation
- Re-ran full end-to-end validation across all services and labs
- Verified Redis, PostgreSQL, Prometheus, Alertmanager, and local webhook behavior
- Verified all nine lab endpoints in vulnerable and hardened mode
- Confirmed generated reports, build transcripts, and prompt artifacts remain excluded from Git

## v1.0.7

- Reworked the visual identity with stronger hand-authored SVG logo assets
- Added logo concept review and final logo selection rationale
- Moved the core Mermaid architecture diagrams into the README
- Expanded README explanation of BoundaryLayer, live infrastructure, labs, observability, and end-to-end validation
- Re-ran full live Docker end-to-end validation
- Confirmed generated reports, build transcripts, and prompt artifacts remain excluded from Git

## v1.0.6

- Aligned API health version with the public release version
- Re-ran full live Docker validation
- Confirmed CI, badges, diagrams, logo assets, and public repository hygiene remain clean

## v1.0.5

- Added hand-authored SVG logo assets and visual identity documentation
- Expanded Mermaid architecture diagrams with end-to-end runtime, lab, observability, trust boundary, and CI flows
- Added end-to-end validation documentation for live Docker testing
- Verified README badges, CI visibility, and public repository hygiene
- Confirmed generated reports, build transcripts, and prompt artifacts remain excluded from Git

## v1.0.4

- Added public demo walkthrough
- Added compact terminal output examples
- Expanded README launch path
- Added launch post draft
- Added repository topic guidance
- Confirmed public repository hygiene checks
- Fixed CI secret scan false positives on workflow and validation scripts

## v1.0.3

- Cleaned public repository provenance
- Removed tooling exposure from public Git history
- Recreated public release tag from clean author history
- Confirmed generated reports and prompt artifacts remain excluded from Git

## v1.0.2

- Added GitHub Actions CI workflow for tests, lint, hygiene checks, and secret scanning
- Added manual Docker validation workflow for full stack `make validate`
- Added pull request template, issue templates, and GitHub release notes config
- Updated release documentation and API version to 1.0.2

## v1.0.1

- Removed editor and tooling artifacts from the public repository
- Added Mermaid architecture diagrams in `docs/DIAGRAMS.md`
- Confirmed generated reports and transcripts remain bundle-only artifacts
- Updated bundle script to exclude `.cursor/` from ZIP output

## v1.0.0

- Public GitHub release stabilization
- Removed generated reports and build transcripts from Git tracking
- Added CHANGELOG, release checklist, and GitHub release documentation
- Polished README with badges and public quick start
- Bundle script generates validation artifacts locally without committing them

## v0.9.0

- File upload sandbox hardening simulation
- Sandbox, egress, active content, hidden instruction, and content wrapping metrics
- File upload Prometheus alert rules
- 149 tests

## v0.8.0

- Prompt Cache Isolation Lab with Redis live mode and fallback
- Cache bleed and isolation metrics
- Prompt cache alert rules

## v0.7.0

- Alertmanager in Docker Compose
- Local alert webhook receiver
- Validated Prometheus to Alertmanager to webhook delivery

## v0.6.0

- SSE Exhaustion Simulation Lab
- Stream cap, orphan, worker, memory, and cleanup metrics

## v0.5.0

- Circuit Breaker Simulation Lab
- Lab-driven circuit breaker gauge and shedding metrics

## v0.4.0

- PostgreSQL Write Storm Lab
- Write storm metrics and alert rules

## v0.3.0

- Live PostgreSQL governance integration
- Orphan detection and deletion audit metrics

## v0.2.0

- Prometheus `/metrics` endpoint
- Live Redis integration for Redis lab
- Alert rules tied to emitted metric names

## v0.1.1

- Release bundle hygiene fixes
- Full source export in ZIP bundles

## v0.1.0

- Initial release with five security labs
- Mock LLM, Docker Compose, and detection config examples
