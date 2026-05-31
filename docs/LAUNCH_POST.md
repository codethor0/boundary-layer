# BoundaryLayer Launch Post (Draft)

Use this draft for LinkedIn, GitHub Discussions, or a project announcement. Edit for your audience before publishing.

---

**BoundaryLayer: an open LLM infrastructure security lab**

Most AI security conversations stop at prompt injection. That is only the first failure mode. After a model is tricked, the real damage happens at infrastructure boundaries: tool routing, session state, authorization, file handling, database writes, streaming, inference backpressure, cache isolation, and alert delivery.

BoundaryLayer is an open-source local lab for simulating those risks in a controlled environment. Each lab runs in vulnerable and hardened modes side by side, emits Prometheus metrics, and routes alerts through Alertmanager to a local webhook for detection practice.

**What it includes**

- Nine deterministic security labs with FastAPI orchestration
- Live Redis and PostgreSQL integration where relevant
- Prometheus metrics and Alertmanager alert routing
- 177 automated tests and a Docker Compose stack
- No paid external LLM APIs required

**Why infrastructure boundaries matter**

LLM applications are distributed systems. A poisoned retrieval can route to the wrong tool. An unsigned session blob can escalate privileges. A shared cache key can bleed data across tenants. Unbounded streams or write storms can take down supporting services. BoundaryLayer makes those failure modes visible locally so platform engineers, security teams, and AI builders can practice detection and hardening without production risk.

**Who it is for**

- Platform and backend engineers building LLM features
- Security and DevSecOps teams evaluating AI system blast radius
- Red and blue teams running controlled exercises
- Educators and compliance teams demonstrating control coverage

**Try it**

Repository: https://github.com/codethor0/boundary-layer

```bash
git clone https://github.com/codethor0/boundary-layer.git
cd boundary-layer
make setup
make up
make validate
```

Start with the demo walkthrough in `docs/DEMO.md` for a five-minute path through vulnerable versus hardened behavior and local alert delivery.

**Feedback welcome**

If you run the labs, I would value feedback on:

- Which boundaries are most useful for your environment
- Gaps in detection coverage or control mapping
- Documentation clarity for onboarding new contributors

BoundaryLayer is for defensive education and secure engineering. It is not a production WAF or a substitute for threat modeling your own systems.

---

Word count: under 900 words.
