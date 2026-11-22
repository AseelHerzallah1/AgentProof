# Architecture decisions — AgentProof

**Status:** Decisions accepted during architecture review, plus items still pending validation.  
**Companion:** [ARCHITECTURE.md](ARCHITECTURE.md)

Nothing here is implemented. Entries record *intent*, not running software.

Format: **Accepted** = we will design and build to this unless a later record supersedes it. **Pending validation** = direction is set, details depend on measurement or an external system. **Open** = deliberately unset until the relevant phase.

---

## Accepted

### AD-001 — Modular monolith, two processes

**Decision:** One repository, one Python backend, **API + worker** processes, shared PostgreSQL. Logical modules are libraries, not microservices.

**Why:** A solo engineer cannot operate a service mesh and still build evaluation, faults, investigation, and runtime labs. Explicit ports give later split options without paying that cost now.

**Rejected:** One process that mixes HTTP and long-running sandboxes (harder cancellation/recovery); many microservices (operational drag).

---

### AD-002 — PostgreSQL is the system of record

**Decision:** Versions, frozen plans, trials, attempts, sandbox resource identity, cancellation, and authoritative outcomes live in PostgreSQL. Evidence events are append-only rows (JSONB envelope + pointers). Blobs live in an artifact store (local FS adapter, GCS in cloud).

**Why:** Investigation needs stable identity and queryable state. Event sourcing the control plane would add complexity without helping the first product questions.

**Rejected:** Kafka/ClickHouse as the evidence plane; OpenTelemetry/Grafana as provenance; storing candidate trees only as database text.

---

### AD-003 — Coordinator interface now; Temporal as an explicit later milestone

**Decision:** Define `WorkflowCoordinator` immediately. First implementation: PostgreSQL-backed attempt state machine in the worker. **Temporal** is a planned engineering milestone after the end-to-end execution path is proven. It must pass recovery, cancellation, and idempotency acceptance tests against the same interface.

**Why:** Temporal is the right class of tool for durable attempts, but leading with it delays the agent/sandbox/verifier contract. Skipping it forever would likely produce a worse in-house workflow engine.

**Invariant:** A killed sandbox is not resumed because workflow history survived. Infrastructure retry is a new attempt.

---

### AD-004 — Two first-class harness modes; implement Mediated first

**Decision:** **Mediated** (trusted runner + Tool Broker + sandbox) and **Contained** (agent process in the sandbox, model egress only through a trusted proxy, policy at FS/process/network) are both architectural modes. Only Mediated is implemented first. Evidence, sandbox identity, and fault types must not assume every tool call hits the broker.

**Why:** The in-house adapter fits Mediated. Real open-source agents often own their tool loop. Encoding only Mediated would force a rewrite at the external-agent milestone.

**Rejected:** Pretending all OSS agents will call our broker unchanged; implementing both harnesses before one E2E path exists.

---

### AD-005 — Investigation is a campaign kind

**Decision:** `evaluation`, `reliability`, `investigation`, and `runtime` share Campaign → Trial → Attempt and the same executor. Investigation adds parent attempt(s), hypothesis, intervention spec, held-constant list, and labeled findings.

**Why:** Failure Provenance & Counterfactual Replay is a core pillar. A second execution path would make the signature workflow the least trusted one.

**Rejected:** Investigation as a separate engine or as UI over logs. Recorded-effect (deterministic trace) replay is deferred, not the first investigation mechanism.

**Finding labels:** `observed` | `correlated` | `experimentally_supported` | `inconclusive`. No unique-root-cause claims without justification.

---

### AD-006 — SandboxManager as a port; profiles are explicit

**Decision:** All execution goes through `SandboxManager`. Profiles include at least:

- `local-docker-dev` — **non-conforming**. Allowed: trusted, deterministic fixtures and contract tests (known-correct/incorrect candidates, scripted workloads, fake-model predetermined edits). **Forbidden:** arbitrary untrusted AI-generated code; using this profile as a security or isolation claim.
- `gke-containerd-gvisor` — first **approved** isolation class. Required for real untrusted execution (live model/agent output, contained OSS agents).
- Later lab profiles (`containerd/runc`, `CRI-O/runc`, `CRI-O/crun`) with isolation class recorded separately

**Why:** Local Docker is necessary to build and test contracts daily. It does not isolate untrusted generated code. gVisor must be validated on its own conformance path. CRI/runtime comparisons need matched labs, not GKE toggling CRI.

**Rejected:** Treating local Docker as equivalent to gVisor; running live LLM-generated code on the dev profile; claiming CRI winners from unmatched managed vs self-managed clusters.

**Clarified:** After baseline approval — fixture-only restriction for `local-docker-dev` is explicit, not merely “non-conforming.”

---

### AD-007 — Two sandboxes and split images for evaluation attempts that verify candidates

**Decision:** For **agent-evaluation** (and reliability/investigation campaigns that independently verify a candidate): agent workspace and a **fresh** candidate environment are distinct resources. Export is path-allowlisted and size-capped. Agent image ≠ verifier image. Hidden checks and reference solutions never enter agent-visible layers.

This two-sandbox contract is **scoped to attempts that require independent candidate verification**. Trusted **runtime** benchmarking campaigns may use a different execution contract (typically a single measured workload sandbox, no candidate export/verify pair) while still using attempt identity, evidence, and cleanup.

**Why:** Independent HTTP verification is the correctness core of the first task family. Hidden tests in the agent image are leakage, not evaluation. Forcing a candidate-verify pair onto trusted microbenchmarks would confound Pillar D measurements.

**Clarified:** After baseline approval — runtime campaigns are not bound to the evaluation sandbox pair.

---

### AD-008 — ModelAccess: fake and direct required; gateway optional

**Decision:** `ModelAccess` has `fake` (tests/CI), `direct` (providers), and later `gateway` backends. AgentProof must run without the LLM Gateway. Evaluation-safe defaults: no cache, no unplanned fallback, record requested vs effective model, never coerce missing usage to zero.

**Why:** The existing gateway is OpenAI-compatible for chat text, but currently lacks tool-calling types; cache and fallback default on (evaluation-unsafe); localhost is not GKE-reachable. Integration is a later, audited optional path.

**Rejected:** Making the gateway an internal module or a Phase 0 dependency.

---

### AD-009 — Typed evidence envelope from day one; small by design

**Decision:** Per-attempt monotonic `seq` is primary timeline order; `ts_utc` is secondary. Envelope includes `schema_version`, `type`, `source`, IDs, `provenance`, payload, artifact IDs, and optional `causal_event_ids`. Artifacts are `sha256` + URI.

**Sequence ownership:** The evidence store (PostgreSQL) is the **sole allocator** of `seq`. Producers (harness, broker, sandbox manager, ModelAccess, verifier, coordinator) call `append` with a draft and **must not** supply `seq`. Allocation is atomic with insert, scoped to `attempt_id` (attempt-row counter updated in the same transaction; unique constraint on `(attempt_id, seq)`). Concurrent appends are serialized by that counter; `seq` is **commit/append order**, not start order and not proof of causality. Explicit `causal_event_ids` record happens-before when producers run concurrently. The counter survives worker restarts because it lives on the attempt row. In-memory or per-producer sequences are forbidden.

**Why:** Pillar C cannot be retrofitted if attempts lack stable event identity. A generic event-sourcing platform is unnecessary. Multiple components emit events for one attempt; client-side counters would race and split after crashes.

**Rejected:** Using Kubernetes events or APM traces as the investigation log; client-assigned `seq`; treating adjacent `seq` values as causal without parent pointers.

**Clarified:** After baseline approval — store-owned `seq`, concurrent-producer rules, causality vs append order.

---

### AD-010 — Tool dispatch state machine and mechanism-agnostic faults

**Decision:** Tool executions use `requested → authorized|denied → dispatched|cancelled|faulted_pre_dispatch → succeeded|failed|timed_out|unknown`. Do not blindly retry `unknown`. `FaultDefinition` is target + mechanism + schedule. First mechanism: deterministic **pre-dispatch** tool error.

**Why:** Pre-dispatch, timeout-after-dispatch, and lost completion are different facts. Broker-shaped faults would not survive Contained mode or later infrastructure faults.

---

### AD-011 — Mutually exclusive primary outcomes

**Decision:** One primary outcome per attempt (`success`, `agent_failure`, `budget_exceeded`, `model_provider_error`, `infrastructure_error`, `invalid_config`, `cancelled`, `unknown_ambiguous`). Secondary contributing events (including injected faults) remain attached.

**Why:** A single pass/fail bit hides the behavior the platform exists to measure.

---

### AD-012 — Python control plane; K8s/Docker only behind ports

**Decision:** FastAPI, Pydantic, PostgreSQL, SQLAlchemy/Alembic for the control plane. Kubernetes Python client and Docker appear only inside sandbox adapters. No extra languages unless a later component truly requires them.

**Why:** Matches existing LLM Gateway skill path; keeps the trusted plane coherent.

---

### AD-013 — CLI/API first; ops dashboards and UI deferred

**Decision:** First interface is authenticated API + CLI. Product evidence ≠ platform telemetry. React UI, Helm, OpenTelemetry, Prometheus/Grafana wait until they reveal measured capabilities. First UI that is likely justified: investigation timeline.

**Why:** A dashboard over empty contracts is not a platform.

---

### AD-014 — Preserve full pillar scope in the architecture

**Decision:** Evaluation, reliability/faults, investigation, runtime intelligence, real open-source agent integration, CRI-O lab, and OCI layer intelligence are **in-scope architectural objectives**. They are sequenced, not optional extras, unless a future decision record drops one.

**Why:** MVP boundaries are intermediate releases, not the product ceiling.

---

### AD-015 — Spend and concurrency bounds are product requirements

**Decision:** Fixed small global concurrency, attempt budgets, resource expiry, sweeper, and a cloud spend/cluster-lifetime kill-switch when a cloud profile exists.

**Why:** Forgotten GKE nodes dominate cost; unbounded agent loops dominate spend. These are part of operational correctness, not later ops polish.

---

### AD-016 — Auth is simple; not multi-tenant

**Decision:** API authentication (e.g. a single API key model) from the first API. No multi-tenant fairness, SSO, or customer isolation in the initial architecture.

**Why:** Retrofitting unauthenticated APIs is avoidable; tenancy is not the current problem.

---

### AD-017 — Linux/WSL2 is the recommended execution host

**Decision:** Container execution should run on Linux (WSL2 or a Linux VM). Confirm the actual machine setup before finalizing tooling.

**Why:** gVisor, kind, containerd, and cluster clients are Linux-native. Docker Desktop on Windows is not an approved isolation profile and must not be treated as one.

---

## Pending validation

These do not reopen the accepted direction; they constrain implementation details.

| ID | Topic | What must be validated | Blocks |
|---|---|---|---|
| PV-001 | Developer environment | WSL2 vs Linux VM vs other; Docker/kind availability | Local sandbox adapter setup |
| PV-002 | GKE Sandbox / gVisor | RuntimeClass, node image, NetworkPolicy to candidate pods, teardown time, available metrics, cost at low concurrency | Approved untrusted profile |
| PV-003 | Verifier networking | Reaching a candidate HTTP service with **no candidate egress**, locally and on GKE | Evaluation E2E on each profile |
| PV-004 | Temporal vs PG coordinator | After E2E exists: crash, cancel-during-tool, duplicate finalization, sweeper-after-restart | Temporal milestone; may defer further if PG recovery tests already pass and ops cost is high |
| PV-005 | LLM Gateway compatibility | Tool-call schema, streaming, timeouts, errors, cache/fallback disable, correlation headers, network path from workers | `gateway` ModelAccess backend |
| PV-006 | First OSS agent | Wrap-ability of Aider, OpenHands, or others: license, tool surface, model client, sandbox assumptions, docker.sock | Contained harness + adapter |
| PV-007 | Runtime lab cost/method | Self-managed K8s bootstrap, matched hardware, residual GKE vs GCE confounders | CRI-O comparison claims |
| PV-008 | OCI measurement conditions | What “cold/warm cache” means on each profile; snapshotter behavior | OCI intelligence claims |
| PV-009 | Task-suite validity | Known-correct/incorrect fixtures; leakage; licenses before any external benchmark import | Publishing or ranking claims |
| PV-010 | gVisor observability limits | Which CPU/memory/IO counters are actually meaningful | Runtime reports for the approved profile |

---

## Open until the relevant phase

| ID | Topic | Why it stays open |
|---|---|---|
| OP-001 | Exact first open-source agent | Must follow PV-006; do not freeze on a name now |
| OP-002 | Recorded-effect replay | Useful later; investigation v1 is controlled re-execution |
| OP-003 | Warm pools, lazy loading, Kata, WASI | Research after baseline measurements |
| OP-004 | LLM-generated hypotheses | Rule-based + human hypotheses first |
| OP-005 | Adaptive extra-trial scheduling | Requires statistical stop rules not yet designed |
| OP-006 | Materialized vs on-read reports | Finalize-time snapshot is enough until analytics hurt |
| OP-007 | Public reproducibility set | Licenses, hidden tests, model spend — policy later |
| OP-008 | Whether to split API/worker into separate deploys | Only if process isolation needs it operationally |
| OP-009 | Secret manager vs env for cloud credentials | Decide with first cloud profile |
| OP-010 | Artifact retention periods and redaction policy details | Contract exists (AD-009); durations wait for real data volumes |

---

## Supersession

If a later decision changes an Accepted item, add a new ID, point at the old one, and update [ARCHITECTURE.md](ARCHITECTURE.md) in the same change. Do not silently edit history.
