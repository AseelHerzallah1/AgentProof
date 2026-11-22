# AgentProof Engineering Implementation Roadmap

**Status:** Planned. **Nothing in this repository is implemented software.**  
**Baseline:** [ARCHITECTURE.md](ARCHITECTURE.md), [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md), [LEARNING_ROADMAP.md](LEARNING_ROADMAP.md), vision blueprint v2.0.

This roadmap sequences the **full four-pillar scope**. It is not a reduced demo plan. Later phases remain in scope even though they are not built first.

---

## 0. How to use this document

**One task at a time.*333333333333* Workflow for every implementation task:

**Understand → Design → Implement → Test → Validate → Log → Commit → Push**

- Discuss the task’s why, contract, and tests **before** changing code.
- After implementation: tests, concise `DEVELOPMENT_LOG.md` entry, review, commit, push.
- Git: `phase-N/task-N.M: concise description`. Author = the engineer’s configured identity only. **No Cursor or AI co-author trailers.**
- Do not commit secrets, hidden verifier checks, or bulky generated artifacts.

**Capability classes**

| Class | Meaning |
|---|---|
| **Implemented** | Running, tested, demoable. Currently: none. |
| **Planned** | In this roadmap; has an exit gate. |
| **Optional milestone** | In scope if compatibility/value holds; not on the critical path. |
| **Experimental research** | Measured investigation; may conclude “no claim” or “not worth productizing.” |

**Local execution rule (all early phases):** `local-docker-dev` runs **trusted/deterministic fixtures only**. No live-model or arbitrary AI-generated code on that profile. Untrusted execution waits for the approved gVisor profile (Phase 6).

**Intended layout** (created in Phase 0; not present yet):

```text
src/agentproof/{domain,evidence,campaign,harness,sandbox,verify,runtime,api,worker}
tests/
fixtures/          # trusted candidates, hidden checks kept out of agent images
DEVELOPMENT_LOG.md
```

---

## 1. Phase map and dependencies

```text
P0 Foundations
  → P1 Fixture verification E2E          ★ independent verification
    → P2 Mediated harness + first fault  ★ fault injection (fixtures)
      → P3 Evaluation & reliability campaigns
        → P4 Operational reliability     ★ cancel / cleanup / idempotency
          → P5 Counterfactual investigation (fixtures)  ★ Pillar C engine
          → P6 GKE/gVisor + first untrusted run
               → Live investigation validation (stochastic traces)
               → Real-agent evaluation campaign (mediated, approved profile)
               → P7 Temporal
               → P8 Contained OSS agent
                    → Real-agent evaluation campaign (OSS adapter)
          P4 also → P9 Runtime lab / CRI-O  (trusted workloads; not gated by P5–P8)
               → P10 OCI layer intelligence
P2 ModelAccess → P11 LLM Gateway (optional, after PV-005)
P5 timeline API → P12 Investigation UI (optional)
```

P5 does **not** require P6–P11. Live investigation and real-agent evaluation campaigns **do** require P6 (and the OSS evaluation campaign also requires P8). P9–P10 do **not** require investigation or OSS agents. P11 does **not** gate any other phase.

**Evidence classes (do not mix in reports):**

| Class | What it is | What it is not |
|---|---|---|
| **Fixture / engine validation** | Deterministic fake-model + known candidates on `local-docker-dev` (P1–P5) | Not a real-agent benchmark; not a model-quality ranking |
| **Live / stochastic evaluation** | Real model-generated (and/or OSS-agent) traces on an **approved** isolation profile | Not bit-for-bit repeatable; reports must show coverage, variability, and uncertainty |

| Phase | Objective (short) | Relative complexity | Class |
|---|---|---|---|
| P0 | Domain, Postgres, evidence `seq`, API/worker | M | Planned |
| P1 | Two-sandbox HTTP verify on trusted fixtures | M–L | Planned |
| P2 | Fake-model mediated loop, broker, pre-dispatch fault | L | Planned |
| P3 | Campaign matrix, reports, 5-task fixture eval | M | Planned |
| P4 | Cancel, crash, sweeper, budgets, coordinator v1 | L | Planned |
| P5 | Investigation campaigns + labeled findings | M | Planned |
| P6 | gVisor profile, spend limits, first live untrusted run; then live eval campaign + live investigation | XL | Planned |
| P7 | Temporal coordinator v2 + same recovery tests | L | Planned |
| P8 | One contained open-source agent | XL | Planned |
| P9 | CRI-O/runc/crun lab, honest measurements | XL | Planned + experimental claims |
| P10 | OCI inventory, diffs, prepare-time evidence | L | Planned |
| P11 | Evaluation-safe gateway backend | M | Optional |
| P12 | Thin investigation timeline UI | M | Optional |

---

## 2. Cross-phase exit gates

Do not start the next phase until the gate is met (exceptions noted).

| After | Gate |
|---|---|
| P0 | Domain + evidence tests pass; `seq` unique under concurrent appends; API rejects unauthenticated calls; worker can no-op an attempt row. |
| P1 | Known-correct fixture **passes** independent HTTP verify; known-incorrect **fails**; both sandboxes destroyed; events stored with store-assigned `seq`. `local-docker-dev` **rejects** an untrusted workload class. |
| P2 | Fake agent repairs a broken starter via brokered tools; verifier passes. Same task with pre-dispatch fault: tool never dispatched; verifier fails; timeline shows `faulted_pre_dispatch`. |
| P3 | Frozen plan expands the illustrative 60-trial matrix; a full **fixture** run produces a coverage-aware **engine-validation** report (success / agent_failure / injected-fault events / missing trials). Report is labeled fixture/deterministic. **Not** a real-agent benchmark. No ranking claim. |
| P4 | Cancel mid-attempt cleans up; worker kill after dispatch yields `unknown` + new attempt; duplicate finalize is rejected; sweeper records orphans. |
| P5 | Failed fixture trial → hypothesis → intervention campaign → comparison with `observed` / `correlated` / `experimentally_supported` / `inconclusive`. |
| P6 | Trusted fixtures pass on gVisor; NetworkPolicy/conformance tests fail closed; one live mediated attempt on gVisor; cluster teardown documented and exercised. |
| P6 live eval | **Real-agent evaluation campaign** (mediated, approved profile, repetitions): report discloses model variability, trial coverage, missing trials, and uncertainty. Not labeled as a fixture result. |
| P6 live investigation | Failed **live** attempt → investigation campaign with repeated trials; findings labeled with stochastic caveats (`observed` / `correlated` / `experimentally_supported` / `inconclusive`). Distinct from P5 fixture validation. |
| P7 | Same P4 recovery tests pass on Temporal; Postgres still owns outcomes; sandbox death is not treated as resume. |
| P8 | Named OSS agent runs on the approved profile; adapter limitations published; no docker.sock. **OSS real-agent evaluation campaign** with the same disclosure rules as the P6 live eval (variability, coverage, uncertainty). |
| P9 | Three lab profiles run the **same trusted** contract; report includes confounders; no silent isolation downgrade. |
| P10 | Two environment revisions show layer inventory/diff and prepare time under a **declared** cache condition. |
| P11 | Gateway path pins model, cache off, fallback off, correlation IDs; direct backend still works. |
| P12 | Timeline UI reads real evidence APIs only (no mock-only demo). |

---

## Phase 0 — Control-plane foundations

**Class:** Planned  
**Objective:** A testable modular monolith with stable IDs, Postgres as system of record, store-owned evidence `seq`, API + worker processes. No containers required.

**Capabilities delivered:** Registry/attempt rows; append-only evidence; local artifact URI; authenticated API skeleton; coordinator **interface** with a Postgres-backed stub.

**Components / tech:** Python, pytest, FastAPI, Pydantic, PostgreSQL, SQLAlchemy, Alembic. Packages: `domain`, `evidence`, `campaign` (stub), `api`, `worker`.

**Prerequisites:** Learning map §1–4. Transfer FastAPI/Postgres from the LLM Gateway. Confirm git author identity (no AI trailers) when the repo is initialized.

**Depends on:** None. **PV-001** must be confirmed **before Phase 1** (not a blocker for P0 code on Windows).

### Tasks

| ID | Objective | Rationale | Touches | Tests / acceptance |
|---|---|---|---|---|
| **0.1** | Repository skeleton: `src/agentproof`, pytest, lint, `pyproject` | One coherent tree before features | repo root | `pytest` collects 0+ tests; import `agentproof` |
| **0.2** | Domain types: IDs, campaign kinds, trial/attempt, outcome taxonomy, workload class (`trusted_fixture` \| `untrusted_agent`) | Language before tables | `domain` | Invalid outcome combinations rejected |
| **0.3** | Alembic + version tables (`TaskVersion`, `AgentVersion`, `EnvironmentVersion`, `RuntimeProfileRevision`, `VerifierVersion`) | Immutable registry | `domain`, migrations | Migration up/down on empty DB |
| **0.4** | Campaign, trial, attempt, `SandboxResource` tables; attempt state column | System of record | migrations | Unique attempt IDs; attempts never deleted |
| **0.5** | `EvidenceWriter.append`: store-assigned `seq`, attempt-row counter, unique `(attempt_id, seq)` | AD-009 | `evidence` | Concurrent appends (threads/async) get unique monotonic `seq`; callers cannot supply `seq` |
| **0.6** | Local filesystem artifact store (`sha256` + URI) | Content-addressed blobs | `evidence` | Put/get by digest; identical bytes → same digest |
| **0.7** | FastAPI app: health + API-key auth | AD-016 | `api` | Missing/wrong key → 401 |
| **0.8** | Register/get versioned task/agent/environment (minimal fields) | First write path | `api`, `domain` | Create is immutable; mutate rejected |
| **0.9** | Worker process + `WorkflowCoordinator` interface; Postgres implementation that can claim an attempt and mark `created→admitted` | Port for P4/P7 | `worker` | Two processes start; claiming is exclusive |
| **0.10** | README (run tests/API) + `DEVELOPMENT_LOG.md` header | Workflow | docs | Engineer can run tests from README |

**End-of-phase demo:** Authenticated API registers a `TaskVersion`. Worker admits an attempt. Two concurrent evidence appends show `seq` 1 then 2. Artifact put/get by digest.

**Risks / unresolved:** PV-001 (host for Phase 1). Exact UUID vs ULID — decide in 0.2, prefer UUID4 unless a strong reason. Do not introduce Temporal, Docker, or Kubernetes here.

---

## Phase 1 — Fixture verification path

**Class:** Planned  
**Objective:** Independent HTTP verification on **trusted fixtures** using `local-docker-dev`. Proves the two-sandbox evaluation contract without an agent and without untrusted code.

**Capabilities delivered:** SandboxManager port + local adapter; agent vs verifier images; export digest; candidate HTTP checks; lifecycle evidence; profile enforcement.

**Components / tech:** Docker Engine (Linux/WSL2), pinned images, `sandbox`, `verify`, hidden checks **outside** agent layers.

**Prerequisites:** Learning map §5–8. **PV-001 confirmed.** Phase 0 gate.

**Depends on:** P0.

### Tasks

| ID | Objective | Rationale | Touches | Tests / acceptance |
|---|---|---|---|---|
| **1.1** | One Python HTTP API fixture: starter (broken), known-correct, known-incorrect; hidden checks stored **not** in the agent image | Benchmark validity | `fixtures/`, `verify` | Hidden-check file is absent from agent image unpack |
| **1.2** | Build/pin agent env image and verifier image by digest | AD-007 | image Dockerfiles, `EnvironmentVersion` | Registry/local digest recorded; tags not used as identity |
| **1.3** | `SandboxManager` port | Single execution seam | `sandbox` | Fake in-memory adapter for unit tests |
| **1.4** | `local-docker-dev` adapter: create, wait_ready, destroy, status; `resource_id` from `attempt_id` + role | First real adapter | `sandbox` | Create is idempotent for same id; destroy is safe twice |
| **1.5** | Refuse `workload_class=untrusted_agent` on `local-docker-dev` | Isolation honesty | `sandbox`, `worker` | Attempt fails `invalid_config`; no container runs agent-generated code |
| **1.6** | Export allowlist + size cap + digest | Bounded candidate | `sandbox` | Path outside allowlist omitted; oversized export fails cleanly |
| **1.7** | Candidate sandbox launch + trusted HTTP verifier | Independent verification | `verify` | Known-correct → `success`; known-incorrect → `agent_failure` |
| **1.8** | Candidate network: no egress; ingress only from verifier (Docker network analogue) | PV-003 local | `sandbox`, `verify` | Egress probe from candidate fails; verifier requests succeed |
| **1.9** | Attempt executor path: persist IDs → candidate sandbox from **known** export → verify → finalize → destroy both roles (agent sandbox may be unused/empty this phase) | Vertical slice | `worker`, `campaign` | Primary outcome persisted; cleanup state recorded |
| **1.10** | Sandbox + verification evidence events (`observed` / `verified`) | Pillar C substrate | `evidence` | Timeline ordered by `seq`; `causal_event_ids` for verify request→result |
| **1.11** | Verifier timeout + failed destroy recorded as infrastructure/cleanup failure | Failure is a result | `verify`, `worker` | Hung candidate is killed; cleanup failure ≠ silent success |

**End-of-phase demo:** Submit a fixture attempt. Known-correct API passes hidden HTTP checks in a **fresh** candidate environment. Events and artifact digest stored. `docker ps` shows no leftover containers. A second attempt with the broken tree fails verification. An attempt marked untrusted is rejected without running.

**Risks / unresolved:** PV-003 on Docker networks may be weaker than K8s NetworkPolicy — document residual, do not claim GKE-equivalent isolation. Windows Docker Desktop is **not** the profile.

---

## Phase 2 — Mediated harness, broker, first fault

**Class:** Planned  
**Objective:** In-house mediated loop using a **fake** model that emits a **predetermined** edit. Tool Broker is mandatory. First Pillar B mechanism: deterministic pre-dispatch tool error. Still no live LLM on local Docker.

**Capabilities delivered:** `ModelAccess.fake`; broker state machine; allowed tools (read/list/write/test-run as designed); agent sandbox → export → existing verifier; `FaultDefinition` + `faulted_pre_dispatch`.

**Components / tech:** `harness`, `ModelAccess`, Tool Broker. Fake plans only on `local-docker-dev`.

**Prerequisites:** Learning map §9–11. Phase 1 gate.

**Depends on:** P1.

### Tasks

| ID | Objective | Rationale | Touches | Tests / acceptance |
|---|---|---|---|---|
| **2.1** | `ModelAccess` port + `fake` backend (scripted tool calls / patch) | CI without providers | `harness` | Deterministic replay of a recorded plan |
| **2.2** | Evaluation-safe telemetry: requested vs effective model, `usage_missing` allowed, no cache/fallback flags default | AD-008 | `harness`, `evidence` | Missing usage not stored as 0 |
| **2.3** | Tool execution state machine (in-memory/DB) without dispatch | AD-010 | `harness` | Illegal transitions rejected |
| **2.4** | Broker authorize + deny (path/tool policy) | Least privilege | `harness` | Write outside allowlist → `denied` |
| **2.5** | Dispatch `exec` into agent sandbox; record dispatched/succeeded/failed | Mediation | `harness`, `sandbox` | Tool result event `causal_event_ids` → request |
| **2.6** | Mediated runner: fake model loop until submit/export, budgets on step/tool count | Runner owns the loop | `harness` | Budget exceed → `budget_exceeded`; sandbox has no model credentials |
| **2.7** | Full fixture repair: broken starter + fake patch via tools → export → verify **success** | Vertical slice with agent workspace | `worker` | Two sandboxes; hidden checks still absent from agent image |
| **2.8** | `FaultDefinition` (target + mechanism + schedule) and pre-dispatch error mechanism | First trustworthy fault | `harness`, `domain` | Fault event; tool state `faulted_pre_dispatch`; **no** sandbox exec |
| **2.9** | Same repair plan under pre-dispatch fault → verify **agent_failure** (fake does not retry unless scripted to) | Pillar B | `worker` | Report distinguishes injected fault event vs primary outcome |
| **2.10** | `unknown` path: simulate lost result after dispatch; **no** automatic retry of that tool | AD-010 | `harness` | New attempt required to continue the trial |
| **2.11** | Block `direct` ModelAccess on `local-docker-dev` | Untrusted-code rule | `harness`, `sandbox` | Config error; no provider HTTP |

**End-of-phase demo:** (1) Fake agent repairs the API; independent verify passes; patch artifact stored. (2) Identical plan with injected pre-dispatch fault; timeline shows fault before dispatch; verify fails. (3) Direct-provider config on local profile is rejected.

**Risks / unresolved:** Exact first tool set (read/write/run tests vs HTTP self-check). Prefer a **small** allowlist. Do not implement Contained mode here. Do not add OpenHands/Aider.

---

## Phase 3 — Evaluation and reliability campaigns

**Class:** Planned  
**Objective:** Typed campaigns, frozen plans, and the illustrative **5 tasks × 2 fake agent versions × 2 conditions × 3 reps = 60 trials** as a **deterministic engine-validation** milestone on fixtures. Coverage-aware reports. **Not** a real-agent benchmark.

**Capabilities delivered:** `evaluation` and `reliability` campaign kinds; CLI submit/inspect/report; honest accounting of missing trials; report metadata that marks results as `fixture` / `deterministic`.

**Components / tech:** `campaign`, CLI, five fixture tasks (pos/neg each).

**Prerequisites:** Learning map §21. Phase 2 gate.

**Depends on:** P2.

### Tasks

| ID | Objective | Tests / acceptance |
|---|---|---|
| **3.1** | Campaign planner: freeze resolved versions into an immutable plan snapshot | Re-resolve after register does not change a frozen plan |
| **3.2** | Expand trial matrix (task × agent × condition × repetition) | 60 logical trials for the illustrative design; IDs stable |
| **3.3** | Four additional HTTP-API tasks with known-correct/incorrect fixtures; validate each pair **before** scoring | 5/5 pos pass, 5/5 neg fail on verifier-only path |
| **3.4** | Two `AgentVersion`s: fake retry-naive vs fake retry-aware | Versions differ only in declared fake plan/policy |
| **3.5** | Run `evaluation` campaign on fixtures (sequential, low concurrency) | All attempts finalize or are marked missing with reason |
| **3.6** | Run `reliability` campaign: normal vs pre-dispatch fault, paired | Report groups by condition, not one global % |
| **3.7** | Report: primary outcomes, secondary fault events, time, fake-usage, coverage, evidence links; **explicit `evidence_class=fixture_deterministic`** | No “best agent” claim; missing trials visible; cannot be mistaken for a live-model benchmark |
| **3.8** | CLI: register, run, inspect attempt timeline, print report | Demo-able without a UI |

**End-of-phase demo:** One command (or short CLI sequence) runs the 60-trial fixture experiment and prints a coverage-aware **engine-validation** report comparing two fake agents under normal vs injected fault, with links to attempt timelines. The report states that these are deterministic fixture results, not real-agent findings.

**Risks / unresolved:** 60 sequential Docker attempts may be slow — keep concurrency = 1 until P4. Do not present P3 output as model or OSS-agent quality. Real-agent evaluation is the **after-P6 / after-P8** milestone.

---

## Phase 4 — Operational reliability (coordinator v1)

**Class:** Planned  
**Objective:** Cancellation, cleanup, idempotency, budgets, and crash semantics as **product tests**, still on local fixtures. Postgres coordinator remains the implementation.

**Capabilities delivered:** Cancel protocol; sweeper; exclusive finalization; recover-on-start; global concurrency; wall/tool budgets.

**Components / tech:** `worker` coordinator v1, sweeper job. No Temporal yet.

**Prerequisites:** Learning map §12. Phase 3 gate (a smaller subset of campaigns is enough if 3.5–3.6 already ran).

**Depends on:** P2 (P3 recommended so cancel is tested against real campaigns).

### Tasks

| ID | Objective | Tests / acceptance |
|---|---|---|
| **4.1** | Cancellation: persist flag; prevent future dispatch; destroy sandboxes; outcome `cancelled` | Cancel before dispatch → no tool exec; resources gone |
| **4.2** | Cancel after dispatch: best-effort kill; residual `unknown` tool recorded if needed | Attempt still terminal `cancelled` or `unknown_ambiguous` per spec; cleanup attempted |
| **4.3** | Exactly-one finalization (unique transition) | Concurrent finalize: one wins, one rejected |
| **4.4** | Worker kill after `dispatched`: recover() marks tool `unknown`, attempt not silently success; retry = **new attempt** | First attempt cost retained |
| **4.5** | Idempotent sandbox create/destroy on restart | No duplicate containers for same `resource_id` |
| **4.6** | Sweeper: expired/orphaned resources; record removed vs failed-to-remove | Injected orphan is found |
| **4.7** | Budgets: wall time, tool count; fake token budget | Exceed → `budget_exceeded`; agent cannot raise limits |
| **4.8** | Global concurrency = 1 (configurable small N) | Second admit waits or queues; never unbounded |
| **4.9** | Coordinator `recover()` on worker start | Crashed `agent_running` attempts reconciled |

**End-of-phase demo:** (1) Cancel a running fixture attempt; no leftover containers. (2) Kill worker after a dispatched tool; restart; timeline shows `unknown`; a new attempt is created rather than mutating the old one. (3) Sweeper removes an intentionally orphaned container and logs it.

**Risks / unresolved:** PV-004 is **not** decided here — these tests **become** the Temporal acceptance suite. Do not start GKE until this gate is green on fixtures (except read-only GCP account setup if desired).

---

## Phase 5 — Failure provenance and counterfactual investigation

**Class:** Planned (core pillar, not optional)  
**Objective:** Investigation as a **campaign kind** on the same executor. This phase is **controlled fixture validation**: cheap, repeatable fake-model traces. It does **not** validate investigation under stochastic live models. That is an explicit milestone **after Phase 6**.

**Capabilities delivered:** Timeline query; hypothesis + intervention spec; follow-up trials; labeled findings; reports marked fixture/deterministic.

**Components / tech:** `campaign` investigation fields, API/CLI. No new runtime.

**Prerequisites:** Learning map §16, §21. Phase 4 gate (P3 minimum if P4 overlap is accepted — prefer P4 so cancelled/unknown attempts appear in timelines).

**Depends on:** P3, P4.

### Tasks

| ID | Objective | Tests / acceptance |
|---|---|---|
| **5.1** | Persist `Hypothesis`, `Intervention`, parent `attempt_id`s, held-constant list, unavoidable diffs | Frozen child plan lists what changed |
| **5.2** | `GET` attempt timeline (events by `seq`, artifacts, outcomes) | CLI/API shows broker/fault/verify chain |
| **5.3** | Create `campaign.kind=investigation` from a failed reliability attempt | Same worker/harness/verifier path |
| **5.4** | Interventions: remove fault; switch fake retry-aware policy; (optional) budget change | Only declared fields change |
| **5.5** | Run repetitions; compare grouped outcomes, time, missing trials | No unique-root-cause sentence generated |
| **5.6** | Finding record with required label enum | Missing label rejected |
| **5.7** | Differential view: first `seq` where two attempts diverge, using `causal_event_ids` where present | Document limitations when fake plans skip steps |

**End-of-phase demo:** Pick a fault-injected **fixture** failure. Show timeline. State hypothesis (“agent never retries after pre-dispatch error”). Run follow-up: fault off vs on, naive vs retry-aware fake agents, N reps. Finding labeled `experimentally_supported` or `inconclusive` with linked attempts. Demo text states this is fixture validation, not live-model evidence.

**Risks / unresolved:** OP-002 recorded-effect replay stays **out**. OP-004 LLM hypotheses stay **out**. UI is P12. Live/stochastic investigation is **not** this phase’s exit gate.

---

## Phase 6 — Approved untrusted profile (GKE + gVisor)

**Class:** Planned  
**Objective:** First **approved** isolation profile. Promote fixture tests onto gVisor, then allow **one** live mediated run with `direct` ModelAccess. Spend and teardown are part of the product.

**Capabilities delivered:** `gke-containerd-gvisor` adapter; NetworkPolicy; GCS artifacts; kill-switch; first untrusted execution; isolation conformance.

**Components / tech:** Terraform (or equivalent IaC), GKE Standard, RuntimeClass/gVisor, Kubernetes Python client **inside** the sandbox adapter, GCS, Artifact Registry.

**Prerequisites:** Learning map §13–14. Phase 4 gate. **PV-002, PV-003 (GKE), OP-009** resolved during this phase, not before P0.

**Depends on:** P4. P5 recommended but not strictly required.

### Tasks

| ID | Objective | Tests / acceptance |
|---|---|---|
| **6.1** | Reproducible cluster module: bounded nodes, labels, destroy-all script, budget alarm | Empty apply/destroy in a throwaway project/sandbox |
| **6.2** | gVisor node pool + RuntimeClass wired in `RuntimeProfileRevision` | Pod spec selects RuntimeClass; fail if missing (no silent runc) |
| **6.3** | GKE `SandboxManager` adapter (create/wait/export/destroy) | Fixture create/destroy; names from `attempt_id` |
| **6.4** | Trust: no automount SA, no privileged, no metadata egress, no K8s API from agent/candidate | Conformance tests fail closed |
| **6.5** | NetworkPolicy: candidate no egress; ingress from verifier only | Egress probe fails; verifier HTTP works (PV-003) |
| **6.6** | Image pull by digest from Artifact Registry | Tag-only create rejected |
| **6.7** | GCS artifact adapter (same `ArtifactRef` interface) | Digest round-trip |
| **6.8** | Spend kill-switch + max cluster lifetime; sweeper against GKE resources | Documented teardown; leftover object count = 0 after destroy |
| **6.9** | **Promote P1–P2 fixture tests** onto gVisor (still trusted fixtures / fake model) | Same pass/fail as local; report profile name |
| **6.10** | Isolation conformance suite (profile must be `gvisor-untrusted`) | Requesting runc for `untrusted_agent` rejected |
| **6.11** | `ModelAccess.direct` (OpenAI-compatible provider) with pin, timeouts, usage-or-missing | Unit tests on recorded HTTP; live smoke optional and budgeted |
| **6.12** | First **untrusted** mediated attempt on gVisor: one task, one live model, budgets, cleanup | Code from the model runs only on gVisor; evidence includes ModelCall + verify |
| **6.13** | Record PV-010: which metrics are actually visible under gVisor | Written limitations in report; no fake cgroup claims |

**End-of-phase demo:** (1) Fixture repair/verify on gVisor matches local outcomes. (2) One live agent attempt edits the API in gVisor; independent verify; cluster and pods gone afterward. (3) Attempt to schedule untrusted work without gVisor **fails**.

This gate is **profile + first untrusted execution**. It is **not** the real-agent evaluation campaign and **not** live investigation validation (tasks 6.14–6.16 below).

**Risks / unresolved:** Cost, GKE Sandbox availability/region, NetworkPolicy vs GKE dataplane, OP-009 secrets. **Do not** run live models on `local-docker-dev` as a shortcut.

### After Phase 6 gate — live evidence milestones

These tasks stay in Phase 6 numbering so later phases are not reshuffled. They **must not** start until the P6 isolation/first-live-attempt gate is green. They use **stochastic live traces** on the approved profile. They are not a repeat of P3 or P5.

| ID | Objective | Tests / acceptance |
|---|---|---|
| **6.14** | **Real-agent evaluation campaign** (mediated in-house adapter + live `direct` model on gVisor): versioned tasks, repetitions, frozen plan | `evidence_class=live_stochastic`; coverage and missing trials reported; **not** labeled as fixture results |
| **6.15** | Report discloses model identity, requested vs effective model, variability (per-task outcome spread), token/time, uncertainty, and sample-size limits | No universal ranking; error bars or equivalent; incomplete trials visible |
| **6.16** | **Live investigation validation:** select a failed **live** attempt; hypothesis; intervention campaign with **repeated** live trials; labeled finding | Distinct from P5; finding text includes stochastic caveats; same executor as evaluation |

**Demo:** A live-model campaign report that cannot be confused with the P3 60-trial fixture report, plus one investigation whose parent attempt is a live trace (not a fake-model fixture).

**Depends on:** P6.1–6.13 and P5 (investigation campaign type). Budgeted; small N is acceptable if uncertainty is disclosed.

---

## Phase 7 — Temporal coordinator v2

**Class:** Planned engineering milestone  
**Objective:** Same `WorkflowCoordinator` interface on Temporal. **Same** P4 acceptance tests must pass. Postgres remains system of record.

**Capabilities delivered:** Durable timers, signals, activity workers; cancel/recover under Temporal.

**Components / tech:** Temporal server (local, then optional GKE), Python SDK. No change to harness/sandbox contracts.

**Prerequisites:** Learning map §15. Phase 4 tests exist. Prefer after P6 if cloud workers are the target; **local Temporal + fixture executor is sufficient to start** this phase in parallel with P6 if cloud cost is a concern.

**Depends on:** P4. Independent of P5/P8/P9.

### Tasks

| ID | Objective | Tests / acceptance |
|---|---|---|
| **7.1** | Local Temporal server + worker process hosting activities | Health check; one no-op workflow |
| **7.2** | Map attempt state machine to workflow; activities keyed by `attempt_id` + name | Idempotent activity replay does not duplicate sandbox create |
| **7.3** | Activities: sandbox, harness, verify, finalize, cleanup — each checks Postgres first | Duplicate activity invocation is a no-op |
| **7.4** | Cancel via workflow signal → same cancel protocol | P4.1–4.2 pass on Temporal |
| **7.5** | Worker/activity crash after dispatch | P4.4 pass: `unknown`, new attempt, no sandbox resume-from-history |
| **7.6** | PV-004 decision record: keep Temporal as default coordinator **or** document why v1 remains default | Explicit AD follow-up; do not run two coordinators silently |

**End-of-phase demo:** Repeat the Phase 4 crash/cancel demo with Temporal driving the worker. Postgres outcomes unchanged in meaning.

**Risks / unresolved:** Ops cost of Temporal on GKE vs local. If P4 already satisfies recovery and Temporal ops dominate, AD-003 still allows deferring production use — but the milestone must be **attempted and tested**, not skipped silently.

---

## Phase 8 — Contained harness and one open-source agent

**Class:** Planned  
**Objective:** One serious external coding agent on the **approved** isolation profile, with published limitations. Evidence/faults remain harness-agnostic.

**Capabilities delivered:** Contained mode; trusted model proxy; one adapter; honest comparison disclosure.

**Components / tech:** `harness` contained adapter, model proxy, chosen OSS agent (name **after** PV-006).

**Prerequisites:** Learning map §17. **P6 gate.** PV-006 research is task 8.1.

**Depends on:** P6 (including 6.14–6.15 report shape). P5 / 6.16 useful for investigating OSS failures. P7 optional.

### Tasks

| ID | Objective | Tests / acceptance |
|---|---|---|
| **8.1** | PV-006 spike: Aider vs OpenHands vs alternative — license, tools, model client, sandbox assumptions, docker.sock | Written comparison; pick one; OP-001 closed |
| **8.2** | Contained sandbox contract: agent process in gVisor; no docker.sock; no control-plane creds | Conformance fail if socket/privileged requested |
| **8.3** | Trusted model proxy as sole egress; credentials stay in proxy | Packet/policy test: agent cannot hit provider directly |
| **8.4** | Adapter: task input, workspace, stop, export | One in-family HTTP-API task completes or fails with evidence |
| **8.5** | Telemetry mapping into `EvidenceEvent` (proxy + sandbox; broker may be partial) | Timeline exists even without broker tool IDs |
| **8.6** | Adapter requirements + limitations doc | Disclosed tool/runtime/prompt/model differences |
| **8.7** | Optional: one independently sourced task revision (pinned, license-checked) — PV-009 | No leakage of hidden checks; or defer with written reason |
| **8.8** | **OSS real-agent evaluation campaign** on the approved profile: repetitions, coverage, variability, uncertainty; disclose adapter/tool/runtime differences | `evidence_class=live_stochastic`; not mixed with P3 fixture scores; limitations page attached |

**End-of-phase demo:** Named OSS agent runs one (or more) API-repair tasks on gVisor via Contained mode. Report shows verify outcome, proxy-correlated model calls, and a limitations page. No docker.sock. Task 8.8’s campaign report treats this as live/stochastic evaluation, not a fixture engine test.

**Risks / unresolved:** Agent may be incompatible without unsafe privileges — then document failure of that candidate and evaluate the next (do not weaken isolation). OP-007 public dataset policy.

---

## Phase 9 — Runtime lab (CRI-O / runc / crun)

**Class:** Planned infrastructure + **experimental** performance claims  
**Objective:** Matched, disposable self-managed Kubernetes profiles for **trusted scripted workloads**. Not a silent substitute for gVisor. Not gated on agents.

**Capabilities delivered:** `runtime` campaign kind; profiles `containerd/runc`, `CRI-O/runc`, `CRI-O/crun`; honest reports.

**Components / tech:** GCE, kubeadm or equivalent, Terraform, `runtime` package, single-sandbox contract (AD-007).

**Prerequisites:** Learning map §18. P4 cleanup/sweeper. **PV-007** during this phase.

**Depends on:** P4 and `SandboxManager` port (P1). **Does not depend on** P5–P8. May follow P6 for GCP skill transfer.

### Tasks

| ID | Objective | Tests / acceptance |
|---|---|---|
| **9.1** | Trusted microbenchmark workload (no model, no generated code) | Deterministic; emits timing events |
| **9.2** | `runtime` campaign type: one sandbox role, no candidate verify pair | Evaluation two-sandbox path unchanged |
| **9.3** | IaC for self-managed cluster; pin k8s/kernel/runtime/CNI/storage/hardware | Destroyable; versions recorded on `RuntimeProfileRevision` |
| **9.4** | Profile: containerd + runc | Workload runs; isolation class `runc-benchmark` |
| **9.5** | Profile: CRI-O + runc | Same contract |
| **9.6** | Profile: CRI-O + crun | Same contract |
| **9.7** | Measurement harness: start vs pull/prepare vs run vs destroy; declared cache state | Report refuses to emit a CRI “winner” without caveats |
| **9.8** | Residual confounders: GKE vs GCE called out; gVisor profile **not** mixed into this comparison | Written methodology |

**End-of-phase demo:** Same trusted contract on three lab profiles. Table of compatibility + timings with cache/hardware/cluster-kind columns. Explicit non-claim if unmatched.

**Risks / unresolved:** Cost of three clusters; PV-007 bootstrap complexity. Claims are experimental until methodology holds.

---

## Phase 10 — OCI layer intelligence

**Class:** Planned  
**Objective:** Inventory and diff environment revisions; measure prepare/start under a declared cache condition.

**Capabilities delivered:** Analyzer library writing evidence; no claim that shared digest ⇒ node cache hit.

**Components / tech:** `runtime` OCI module, registry APIs, Artifact Registry.

**Prerequisites:** Learning map §19. Pinned images from P1/P6. **PV-008** during this phase.

**Depends on:** P1 image pinning; stronger with P6/P9 registries.

### Tasks

| ID | Objective | Tests / acceptance |
|---|---|---|
| **10.1** | Inventory: platform, manifest/config digests, layer descriptors, compressed sizes, diff IDs | Golden test against a known fixture image |
| **10.2** | Diff two `EnvironmentVersion`s: shared/new/removed blobs | Explains a real fixture image change |
| **10.3** | Prepare/start timing with **declared** cache/network/runtime | Two runs labeled cold vs warm (defined in-task) |
| **10.4** | Report language: digest identity ≠ node cache; workspace edits ≠ layers | Tests or snapshot of report text constraints |
| **10.5** | Experimental backlog only: whiteouts, lazy loading — **out** unless a follow-up AD | No silent scope creep |

**End-of-phase demo:** Two environment revisions; layer graph diff; prepare-time under a named cache condition.

**Risks / unresolved:** PV-008 definition of warm cache per snapshotter. OP-003 remains research, not this phase’s exit.

---

## Phase 11 — LLM Gateway integration (optional)

**Class:** Optional milestone  
**Objective:** `ModelAccess.gateway` after a **compatibility audit**. AgentProof stays runnable on `fake` and `direct`. Tool execution stays in AgentProof.

**Capabilities delivered:** Evaluation-safe gateway policy consumption; correlation of gateway request IDs to attempts.

**Components / tech:** Existing LLM Gateway repo (separate changes), AgentProof gateway backend.

**Prerequisites:** Learning map §20. **PV-005**. Prefer P6 so network path is real (localhost ≠ GKE).

**Depends on:** P2 `ModelAccess` port. **Not** on P8–P10.

### Tasks

| ID | Objective | Tests / acceptance |
|---|---|---|
| **11.1** | Audit gateway: tools, streaming, timeouts, errors, cache, fallback, bodies vs metadata | Written gap list vs AgentProof needs |
| **11.2** | Gateway-repo work (if proceeding): tool schema, pin-model, cache-off, fallback-off, correlation headers | Gateway tests in **that** repo |
| **11.3** | AgentProof `gateway` backend | Unit tests against recorded eval-safe responses |
| **11.4** | Authenticated path from worker (local and/or GKE) | Failure if gateway unreachable is `model_provider_error` |
| **11.5** | One gVisor (or fixture-fake-only if tools still missing) campaign through gateway vs direct | Disclose remaining gaps; direct still default |

**End-of-phase demo:** Model calls for a budgeted attempt go through the gateway with cache/fallback off; AgentProof timeline shows provider identity and gateway request id. Direct backend still passes the same harness tests.

**Risks / unresolved:** Tool-calling may be a large gateway project. If 11.1 says “not worth it yet,” stop after the audit — that is a valid completion of the milestone’s **decision**, not a silent drop of the seam.

---

## Phase 12 — Investigation UI (optional)

**Class:** Optional  
**Objective:** Thin UI over **real** timeline/investigation APIs after P5.

**Capabilities delivered:** Attempt timeline, launch investigation, show finding labels. Not a leaderboard product.

**Depends on:** P5. Stronger after P6 live traces.

### Tasks

| ID | Objective | Tests / acceptance |
|---|---|---|
| **12.1** | Read-only timeline page from API | Empty/error states; no mock-only happy path |
| **12.2** | Create investigation + view comparison | Labels visible; no auto “root cause” copy |
| **12.3** | Auth using existing API key | Unauthenticated denied |

**Out:** Helm, OTel, Grafana as the investigation surface (AD-013).

---

## 3. Explicitly not in this roadmap’s phases

These remain **architecture-open** or **experimental research**. They are not forgotten; they are not scheduled as delivery gates:

| Item | Class | When to reopen |
|---|---|---|
| Recorded-effect replay (OP-002) | Experimental | After P5 is real |
| Warm pools, stargz/Nydus, Kata, WASI (OP-003) | Experimental | After P9–P10 measurements |
| LLM-generated hypotheses (OP-004) | Out until evidence quality is high | After P5 |
| Adaptive extra-trial scheduling (OP-005) | Out | After §21 statistics exist in reports |
| Multi-tenant / SSO | Out | Not current architecture |
| Helm / Prometheus / Grafana | Optional ops | Only if control-plane ops demand it |

---

## 4. Pillar coverage (so scope cannot quietly shrink)

| Pillar | First demo | Hardening |
|---|---|---|
| **A Evaluation** | P1 verify + **P3 fixture engine-validation** (60-trial) | **P6.14–6.15 live mediated campaign**; **P8.8 OSS campaign** |
| **B Reliability** | P2 pre-dispatch fault | P4 cancel/unknown, later mechanisms only if needed |
| **C Provenance / counterfactual** | P0–P2 evidence; **P5 fixture investigation** | **P6.16 live investigation**; P12 UI optional |
| **D Runtime intelligence** | P1 digest pinning; P6 gVisor evidence | **P9 CRI-O lab, P10 OCI** |

---

## 5. Suggested implementation policy

1. **Do not start a task until the previous task in-phase is committed**, unless the engineer explicitly parallelizes independent tasks (rare).
2. **Do not skip exit gates** to “get to Kubernetes faster.”
3. **P9 may proceed after P4** even if P5–P8 are in progress, if cloud budget is managed separately.
4. **P11 audit (11.1)** may occur anytime after P2; implementation waits on the audit.
5. Before **0.1**, confirm git identity and (for P1) PV-001. Repository hosting (GitHub) is an engineer action, not a code task in this file.

**First implementation task after approval of this roadmap and of the Task 0.1 design:** **0.1 Repository skeleton**.
