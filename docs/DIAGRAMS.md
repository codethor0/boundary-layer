# Architecture Diagrams

Mermaid diagrams for BoundaryLayer system architecture, lab execution, trust boundaries, and observability.

## System Architecture

BoundaryLayer runs as a Docker Compose stack. The API orchestrates nine security labs and exposes Prometheus metrics. Alertmanager routes firing alerts to a local webhook for validation.

```mermaid
flowchart LR
    Client[Client / curl / Browser] --> API[BoundaryLayer API]
    API --> Labs[Lab Modules]
    API --> MockLLM[Mock LLM]
    API --> Redis[(Redis)]
    API --> Postgres[(PostgreSQL)]
    API --> Metrics[/Prometheus Metrics Endpoint/]

    Prometheus[Prometheus] -->|scrapes /metrics| API
    Prometheus -->|sends alerts| Alertmanager[Alertmanager]
    Alertmanager -->|local webhook| Webhook[Alert Webhook]

    Labs --> ToolRouter[Tool Router Lab]
    Labs --> RedisLab[Redis Tampering Lab]
    Labs --> AuthZ[AuthZ Lab]
    Labs --> FileUpload[File Upload Lab]
    Labs --> Governance[Governance Lab]
    Labs --> WriteStorm[PostgreSQL Write Storm Lab]
    Labs --> CircuitBreaker[Circuit Breaker Lab]
    Labs --> SSE[SSE Exhaustion Lab]
    Labs --> PromptCache[Prompt Cache Isolation Lab]
```

## Lab Execution Flow

Each lab request is validated, executed in vulnerable or hardened mode, and recorded in Prometheus metrics. Validation scripts confirm end-to-end alert delivery through the local webhook.

```mermaid
sequenceDiagram
    participant User
    participant API as BoundaryLayer API
    participant Lab as Lab Module
    participant Metrics as Metrics Registry
    participant Prom as Prometheus
    participant AM as Alertmanager
    participant Hook as Alert Webhook

    User->>API: POST /labs/{lab}/run
    API->>API: Validate mode and request fields
    API->>Lab: Execute vulnerable or hardened mode
    Lab->>Metrics: Emit counters and gauges
    Lab-->>API: Return lab result JSON
    API-->>User: blocked, risk, control, events, summary
    Prom->>API: Scrape /metrics
    Prom->>AM: Send matching alert
    AM->>Hook: POST /alerts
    Hook-->>AM: 200 OK
```

## Trust Boundary Model

Untrusted inputs cross validation and mode-specific policy before touching state or telemetry. Detection rules consume emitted metrics and route alerts locally.

```mermaid
flowchart TB
    subgraph Untrusted[Untrusted Inputs]
        Requests[Lab Requests]
        Retrieved[Retrieved Content]
        FileMeta[Synthetic File Metadata]
        PromptPrefix[Synthetic Prompt Prefix]
        WorkUnits[Synthetic Work Units]
    end

    subgraph Boundary[Boundary Controls]
        Validation[Request Validation]
        Policy[Mode-Specific Policy]
        Wrapping[Untrusted Content Wrapping]
        Namespacing[Tenant Namespacing]
        Throttling[Budgets and Backpressure]
    end

    subgraph State[State and Telemetry]
        Redis[(Redis)]
        Postgres[(PostgreSQL)]
        Metrics[Prometheus Metrics]
    end

    subgraph Detection[Detection and Alerting]
        Rules[Prometheus Alert Rules]
        Alertmanager[Alertmanager]
        Webhook[Local Alert Webhook]
    end

    Requests --> Validation
    Retrieved --> Wrapping
    FileMeta --> Validation
    PromptPrefix --> Namespacing
    WorkUnits --> Throttling

    Validation --> Policy
    Policy --> Redis
    Policy --> Postgres
    Policy --> Metrics

    Metrics --> Rules
    Rules --> Alertmanager
    Alertmanager --> Webhook
```

## Observability Pipeline

The API exposes `/metrics`. Prometheus evaluates alert rules, Alertmanager routes matches to the webhook, and `validate.sh` confirms delivery after triggering a lab condition.

```mermaid
flowchart LR
    API[BoundaryLayer API] -->|exposes /metrics| Prom[Prometheus]
    Prom -->|evaluates rules| Rules[Alert Rules]
    Rules -->|fires alert| AM[Alertmanager]
    AM -->|POST /alerts| Hook[Alert Webhook]
    Validate[validate.sh] -->|triggers lab condition| API
    Validate -->|polls /alerts| Hook
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for service ports, metric names, and lab behavior details.
