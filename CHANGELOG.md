# Changelog

All notable changes to BoundaryLayer are documented here.

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
