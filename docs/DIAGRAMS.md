# Architecture Diagrams

Mermaid diagrams for BoundaryLayer runtime topology, lab flows, trust boundaries, observability, and release validation. All diagrams reflect current v1.0.5 behavior.

See [ARCHITECTURE.md](ARCHITECTURE.md) for ports, metrics, and lab details.

## 1. System Architecture

```mermaid
flowchart LR
    User[User / curl] --> API[BoundaryLayer API :8000]
    API --> Labs[Lab Modules]
    API --> MockLLM[Mock LLM :8080]
    API --> Redis[(Redis :6379)]
    API --> Postgres[(PostgreSQL :5432)]
    API --> Metrics[/GET /metrics/]

    Prometheus[Prometheus :9090] -->|scrape 15s| API
    Prometheus -->|firing alerts| AM[Alertmanager :9093]
    AM -->|POST /alerts| Hook[Alert Webhook :8081]

    GH[GitHub Actions CI] -->|tests lint hygiene| Repo[boundary-layer repo]
```

## 2. Docker Compose Runtime Topology

```mermaid
flowchart TB
    subgraph Host[Docker Compose Network]
        API[api :8000]
        Mock[mock-llm :8080]
        Redis[(redis :6379)]
        PG[(postgres :5432)]
        Prom[prometheus :9090]
        AM[alertmanager :9093]
        Hook[alert-webhook host 8081 to 8080]
    end

    API --> Mock
    API --> Redis
    API --> PG
    Prom -->|scrape api:8000| API
    Prom --> AM
    AM --> Hook
```

## 3. Lab Execution Sequence

```mermaid
sequenceDiagram
    participant User
    participant API as BoundaryLayer API
    participant Lab as Lab Module
    participant Metrics as Metrics Registry
    participant Infra as Redis or PostgreSQL

    User->>API: POST /labs/{lab}/run
    API->>API: Validate mode and fields
    API->>Lab: Execute vulnerable or hardened path
    Lab->>Infra: Live or fallback interaction
    Lab->>Metrics: Record counters and gauges
    Lab-->>API: Structured result dict
    API->>API: Strip internal metric keys
    API-->>User: lab mode blocked risk control events summary
```

## 4. Observability and Alerting Pipeline

```mermaid
flowchart LR
    API[API /metrics] -->|scrape| Prom[Prometheus]
    Prom --> Rules[alerts.yml rules]
    Rules -->|firing| AM[Alertmanager]
    AM --> Hook[Local webhook :8081]
    Validate[make validate] -->|trigger circuit breaker| API
    Validate -->|poll GET /alerts| Hook
```

## 5. Trust Boundary Model

```mermaid
flowchart TB
    subgraph Untrusted[Untrusted Inputs]
        Req[Lab requests]
        Retrieved[Retrieved content]
        FileMeta[Synthetic file metadata]
        Prefix[Synthetic prompt prefix]
        Work[Work units and streams]
    end

    subgraph Controls[Boundary Controls]
        Val[Request validation]
        Policy[Mode policy]
        Wrap[Untrusted wrapping]
        NS[Tenant namespacing]
        Budget[Write and stream budgets]
        CB[Circuit breaker]
    end

    subgraph State[State and Telemetry]
        Redis[(Redis)]
        PG[(PostgreSQL)]
        M[Prometheus metrics]
    end

    subgraph Detect[Detection]
        Rules[Alert rules]
        AM[Alertmanager]
        Hook[Local webhook]
    end

    Req --> Val
    Retrieved --> Wrap
    FileMeta --> Val
    Prefix --> NS
    Work --> Budget
    Work --> CB

    Val --> Policy
    Policy --> Redis
    Policy --> PG
    Policy --> M
    M --> Rules --> AM --> Hook
```

## 6. Redis State Tampering Flow

```mermaid
flowchart TB
    Start[POST /labs/redis/run] --> Mode{mode}

    Mode -->|vulnerable| VStore[Store unsigned session blob]
    VStore --> VTamper[Accept tampered role admin]
    VTamper --> VOut[blocked false privilege escalation]

    Mode -->|hardened| HStore[Store HMAC-signed session]
    HStore --> HTamper[Reject tampered blob]
    HTamper --> HOut[blocked true HMAC control]

    VOut --> Redis[(Redis boundary_layer:lab:redis:*)]
    HOut --> Redis
```

## 7. PostgreSQL Governance Flow

```mermaid
flowchart TB
    Gov[POST /labs/governance/run] --> Mode{mode}

    Mode -->|vulnerable| VDel[Delete prompt_requests only]
    VDel --> VOrphan[Orphan rows in downstream tables]
    VOrphan --> VMetric[orphan_records metric]

    Mode -->|hardened| HDel[Cascade deletion audit]
    HDel --> HAudit[Insert deletion_audit row]
    HAudit --> HMetric[governance_deletion_audits metric]

    VOrphan --> PG[(PostgreSQL lifecycle tables)]
    HAudit --> PG
```

Downstream tables include `prompt_logs`, `tool_records`, `evaluation_queue`, and `training_queue`.

## 8. PostgreSQL Write Storm Flow

```mermaid
flowchart LR
    WS[POST /labs/postgres-write-storm/run] --> Req[requested_writes]
    Req --> Mode{mode}

    Mode -->|vulnerable| VFull[Insert full batch default 250]
    VFull --> VMetric[write_storm_events metric]

    Mode -->|hardened| HCap[Cap inserts at 50]
    HCap --> HBlock[Block excess writes]
    HBlock --> HMetric[blocked_writes metric]

    VFull --> PG[(write_storm_events)]
    HCap --> PG
```

## 9. Circuit Breaker State Flow

```mermaid
stateDiagram-v2
    [*] --> Evaluate: requested work units
    Evaluate --> Closed: hardened and within safe capacity 100
    Evaluate --> Open: hardened and exceeds safe capacity
    Evaluate --> ClosedVuln: vulnerable accepts all work
    Closed --> EmitClosed: metric state 0
    Open --> Shed: shed excess work units
    Shed --> EmitOpen: metric state 1
    EmitOpen --> Alert: BoundaryLayerInferenceCircuitBreakerOpen
    ClosedVuln --> EmitClosed
```

## 10. SSE Exhaustion Flow

```mermaid
flowchart TB
    SSE[POST /labs/sse-exhaustion/run] --> Mode{mode}

    Mode -->|vulnerable| VAccept[Accept all requested streams]
    VAccept --> VOrphan[Report orphaned streams]
    VOrphan --> VMetrics[active and orphaned gauges]

    Mode -->|hardened| HCap[Apply stream cap 50]
    HCap --> HReject[Reject excess streams]
    HReject --> HCleanup[Apply cleanup]
    HCleanup --> HMetrics[rejected and cleanup metrics]
```

## 11. Prompt Cache Isolation Flow

```mermaid
flowchart TB
    PC[POST /labs/prompt-cache-isolation/run] --> Mode{mode}

    Mode -->|vulnerable| VKey[Global cache key]
    VKey --> VBleed[Tenant B hits Tenant A entry]
    VBleed --> VMetric[cross_tenant_bleed metric]

    Mode -->|hardened| HKey[tenant_scoped keys]
    HKey --> HBlock[No cross-tenant hit]
    HBlock --> HMetric[isolation_applied metric]

    VKey --> Redis[(Redis prompt_cache namespace)]
    HKey --> Redis
```

## 12. File Sandbox Hardening Flow

```mermaid
flowchart TB
    FU[POST /labs/file-upload/run] --> Meta[Synthetic file metadata]
    Meta --> Mode{mode}

    Mode -->|vulnerable| VExtract[Unsafe extraction to context]
    VExtract --> VEgress[Allow simulated egress]

    Mode -->|hardened| HSandbox[Apply sandbox policy]
    HSandbox --> HActive[Block active content if present]
    HActive --> HEgress[Block egress if attempted]
    HEgress --> HWrap[Wrap extracted content as untrusted]
    HWrap --> HMetrics[sandbox egress wrap metrics]
```

## 13. CI and Release Validation Flow

```mermaid
flowchart LR
    Push[Push or PR to main] --> GHA[GitHub Actions CI]
    GHA --> Test[make test 149]
    GHA --> Lint[make lint]
    GHA --> Hygiene[tracked artifact scan]
    GHA --> Secret[secret pattern scan]

    Manual[Manual workflow] --> DockerVal[Docker Validate]
    DockerVal --> Up[make up]
    DockerVal --> Val[make validate]

    Release[Release owner] --> Local[Local make validate authoritative]
    Release --> Tag[git tag vX.Y.Z]
    Tag --> GHRel[GitHub Release]
```
