# Technology Learning Map — AgentProof

**Status:** Study guide ordered by engineering dependencies. Not an implementation task list.  
**Companions:** [ARCHITECTURE.md](ARCHITECTURE.md), [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md)

Learn each item when the architecture needs it. Transfer from the existing LLM Gateway (FastAPI, Pydantic, PostgreSQL, pytest, structured logs) rather than re-learning those from scratch. Depth targets what AgentProof will actually build.

---

## How to use this map

- **Before implementing:** the minimum you must be able to explain and test.
- **During implementing:** details that only become real with a working component.
- Later layers assume earlier ones. Do not start GKE, Temporal, CRI-O, or OSS-agent internals before the control-plane and fixture E2E contracts exist.

```text
Domain + evidence + Postgres
        → local Docker fixtures + HTTP verifier
            → mediated harness (fake model, broker, faults)
                → cancellation / idempotency / budgets
                    → GKE + gVisor (first untrusted profile)
                        → Temporal recovery milestone
                            → investigation campaigns (same substrate)
                                → contained OSS agent
                                    → runtime lab / CRI-O / OCI
                                        → optional LLM Gateway backend
```

---

## 1. Domain, identity, and campaign model

**Purpose.** Stable language for versions, campaigns, trials, attempts, outcomes, and investigation-as-campaign. Everything else hangs off these IDs.

**Prerequisites.** Basic relational modeling; immutability vs mutable runtime state.

**Before implementing.** Trial vs attempt; frozen plan snapshots; mutually exclusive primary outcomes; why investigation is a campaign kind; why infrastructure retry must not mutate the first attempt.

**Learn during.** Concrete ID formats, version-row shape, how a 5-task × 2-agent matrix expands.

**Depends on this.** All packages; Pillars A–C; reports; later Temporal activity keys.

---

## 2. PostgreSQL as system of record (SQLAlchemy, Alembic)

**Purpose.** Source of truth for registry, plans, attempt state, sandbox resource identity, cancellation, outcomes, and evidence rows.

**Prerequisites.** Transactions, unique constraints, foreign keys. Gateway work already covers the Python stack.

**Before implementing.** Idempotent writes; unique transition for finalization; attempt-row locking for concurrent updates; why the control plane is **not** event-sourced.

**Learn during.** Alembic workflow for this repo, JSONB payload versioning, exact attempt state-machine columns.

**Depends on this.** API, worker, evidence `seq`, coordinator v1, every later adapter.

---

## 3. Evidence log, `seq`, and content-addressed artifacts

**Purpose.** Pillar C substrate: typed envelope, store-assigned monotonic `seq`, artifact `sha256` + URI.

**Prerequisites.** §1–2; append-only vs overwrite; hash identity.

**Before implementing.** Store owns `seq`; concurrent producers must not mint sequences; `seq` is append order, not causality; `causal_event_ids` for request→dispatch→result; provenance labels (`planned` / `observed` / `reported_by_agent` / `verified` / `inferred`); finding labels for investigations.

**Learn during.** Transaction that increments the attempt counter and inserts the event; local FS artifact adapter; redaction as a new event.

**Depends on this.** Timeline, investigation, reports, every emitter (harness, broker, sandbox, verifier).

---

## 4. FastAPI control plane and worker process split

**Purpose.** Authenticated submit/inspect/cancel (API) vs long-running attempts (worker), one repo.

**Prerequisites.** Gateway-level FastAPI/Pydantic; process vs request lifecycle.

**Before implementing.** Why the API must not run agent loops; command/ID stability; simple API-key auth (AD-016); how the worker claims admitted attempts.

**Learn during.** App layout, CLI over the same commands, failure modes when the worker dies mid-attempt (feeds coordinator v1).

**Depends on this.** All operator-facing workflows; later Temporal worker hosting.

---

## 5. Linux/WSL2 and local container tooling

**Purpose.** Host for `local-docker-dev` fixtures. Not an isolation story.

**Prerequisites.** Shell, filesystems, bind mounts vs copy-in.

**Before implementing.** Confirm PV-001 (WSL2 vs Linux VM). Docker as a **dev adapter**, not a security boundary. Image digest vs tag.

**Learn during.** Day-to-day image build/run, volume and network behavior of the fixture profile.

**Depends on this.** Local sandbox adapter; later kind/kubectl familiarity.

---

## 6. OCI image basics (enough for fixtures)

**Purpose.** Pin `EnvironmentVersion` by digest; build approved task images; later OCI intelligence builds on the same terms.

**Prerequisites.** Layers as tarballs; manifest vs config vs blobs (conceptual).

**Before implementing.** Digest identity; agent image ≠ verifier image; hidden checks must not appear in agent layers; candidate edits are not OCI layers.

**Learn during.** A real pinned fixture image; reproducing a pull by digest.

**Depends on this.** Sandbox create; verification; later Pillar D inventory.

**Defer:** whiteouts, snapshotters, stargz — until the OCI analyzer phase.

---

## 7. SandboxManager and `local-docker-dev`

**Purpose.** Port for create / wait / exec / export / destroy / status. First adapter: trusted fixtures only.

**Prerequisites.** §5–6; attempt-scoped `resource_id`.

**Before implementing.** Allowed workload class (deterministic fixtures, known candidates, fake-model predetermined edits). **Forbidden:** arbitrary untrusted AI-generated code on this profile. Cleanup and idempotent create/destroy.

**Learn during.** Real fixture lifecycle, export allowlist/size cap, orphaned-container failure cases.

**Depends on this.** Verifier E2E on fixtures; later GKE adapter (same port).

---

## 8. Independent HTTP verification

**Purpose.** Authoritative outcome for Python HTTP API repair tasks.

**Prerequisites.** HTTP semantics; §7; hidden-check storage.

**Before implementing.** Verifier is trusted, candidate is not; fresh environment per verifying attempt; no candidate egress; ingress only from verifier; known-correct and known-incorrect fixtures must pass/fail before any agent score counts.

**Learn during.** How the candidate process is launched, health wait, timeout, and teardown; NetworkPolicy analogue on Docker networks vs GKE.

**Depends on this.** Pillar A; investigation of verifier-rejected attempts; two-sandbox evaluation contract (not runtime benchmarks).

---

## 9. ModelAccess (fake, then direct providers)

**Purpose.** Pin model identity, record usage/errors, keep the gateway optional.

**Prerequisites.** OpenAI-compatible chat/tool-call JSON; timeouts; your gateway’s limits (no tools, cache/fallback on by default).

**Before implementing.** `fake` backend for CI; evaluation-safe defaults (no cache, no fallback, missing usage ≠ 0); requested vs effective model; correlation IDs.

**Learn during.** Live provider error shapes; streaming vs non-streaming (use what the harness actually needs); token accounting gaps.

**Depends on this.** Mediated runner; later `gateway` backend (PV-005).

---

## 10. Mediated agent loop and tool-calling contract

**Purpose.** First in-house adapter: trusted runner owns the model/tool loop.

**Prerequisites.** §9; function/tool calling as model JSON, not as “the agent has root.”

**Before implementing.** Step vs model call vs tool request; budgets enforced **outside** the agent; runner never places provider credentials in the sandbox.

**Learn during.** Real multi-step traces; how a predetermined fake tool plan maps to broker states.

**Depends on this.** Pillars A–C mediated path; not a substitute for Contained mode.

---

## 11. Tool broker, dispatch states, and first fault

**Purpose.** Authorization, mediation, Pillar B’s first trustworthy fault (pre-dispatch error).

**Prerequisites.** §10; state machines; AD-010.

**Before implementing.** `requested → authorized|denied → dispatched|cancelled|faulted_pre_dispatch → succeeded|failed|timed_out|unknown`. Never blindly retry `unknown`. `FaultDefinition` is target + mechanism + schedule, even when only pre-dispatch is implemented.

**Learn during.** Timing of evidence appends vs sandbox exec; cancellation after dispatch; unknown-completion after a worker crash.

**Depends on this.** Reliability campaigns; investigation of injected-fault trials.

---

## 12. Budgets, cancellation, cleanup, coordinator v1

**Purpose.** Operational correctness as product behavior, before Temporal.

**Prerequisites.** Attempt state machine (ARCHITECTURE §9.2); idempotency ownership table.

**Before implementing.** Persist `attempt_id` and sandbox IDs **before** create; cancel prevents future dispatch and still cleans up; sweeper records failures to delete; killed process ≠ resumed workflow.

**Learn during.** Crash tests on the fixture path; duplicate finalization attempts; expiry of abandoned resources.

**Depends on this.** Any cloud profile; Temporal acceptance tests (same cases, stronger driver).

---

## 13. Kubernetes execution model (when leaving the fixture profile)

**Purpose.** Drive real sandboxes via the same `SandboxManager` port.

**Prerequisites.** Pod, container, image pull, restart policy, resource limits, namespaces. Do not start from Operators/meshes.

**Before implementing.** RuntimeClass does **not** install a CRI; service accounts and automount; why agent pods must not reach the API or cloud metadata; stable names from `attempt_id`.

**Learn during.** Actual pod latency, pull vs start timestamps, failure reasons (`ImagePullBackOff`, OOM, preemption).

**Depends on this.** GKE adapter; later runtime lab.

---

## 14. GKE Sandbox / gVisor (first approved untrusted profile)

**Purpose.** Isolation for live model/agent-generated code and contained OSS agents.

**Prerequisites.** §13; syscall isolation vs “a container is enough”; PV-002.

**Before implementing.** What gVisor intercepts; what cgroup/metrics you will **not** get; NetworkPolicy for verifier→candidate and default-deny egress; spend/cluster lifetime kill-switch; fail-closed conformance.

**Learn during.** Node pool/RuntimeClass wiring, teardown cost, residual differences vs local fixtures.

**Depends on this.** Any untrusted execution; honest isolation claims; contained harness.

---

## 15. Durable workflows (Temporal) as coordinator v2

**Purpose.** Recovery, timers, and activity retries after the fixture/untrusted E2E path exists.

**Prerequisites.** §12; idempotent activities; AD-003.

**Before implementing.** Workflow vs activity vs worker; signals for cancel; **do not** retry non-idempotent dispatch; PostgreSQL remains system of record; sandbox death is not workflow resume.

**Learn during.** SDK patterns, local Temporal server ops, the same crash/cancel tests as coordinator v1.

**Depends on this.** Long-running campaigns at cloud concurrency; not Pillar C’s evidence model.

---

## 16. Investigation methodology (product, not a new runtime)

**Purpose.** Pillar C: hypothesis, intervention, controlled re-execution, uncertainty labels.

**Prerequisites.** Evidence envelope; campaign kinds; statistical humility (repetitions ≠ task diversity).

**Before implementing.** Counterfactual = new real attempts, not alternate-history replay; held-constant vs unavoidable diffs; finding labels; no unique-root-cause theater.

**Learn during.** Diffing two attempt timelines; what to freeze when the live model is stochastic.

**Depends on this.** Signature demo; later UI timeline. **Does not** depend on Temporal, CRI-O, or the gateway.

---

## 17. Contained harness and open-source agents

**Purpose.** Real agents that own their tool loop, without granting docker.sock or control-plane credentials.

**Prerequisites.** Approved isolation profile (§14); model proxy idea; PV-006. Do not freeze the agent name now.

**Before implementing.** Mediated vs Contained (ARCHITECTURE §5); how the candidate agent gets a workspace; where model credentials live (proxy, never in the agent); what telemetry you can actually capture if the broker is bypassed.

**Learn during.** One adapter’s real CLI/SDK, license, file/network surface, and failure modes.

**Depends on this.** External-credibility milestone. Evidence/fault types must already be harness-agnostic.

---

## 18. Runtime terminology, CRI-O lab, and honest measurement

**Purpose.** Pillar D comparisons: CRI vs OCI runtime vs snapshotter vs cluster management.

**Prerequisites.** §13; matched-experiment thinking; AD-006/AD-007 (runtime campaigns need **not** use two evaluation sandboxes).

**Before implementing.** Why GKE cannot be switched to CRI-O; why GKE vs GCE confounds “the CRI”; trusted scripted workloads vs stochastic agents; isolation class `runc-benchmark` ≠ `gvisor-untrusted`.

**Learn during.** Bootstrap cost (Terraform/GCE), pin list (kernel, CNI, storage, hardware), residual caveats in reports.

**Depends on this.** CRI-O/runc/crun milestone. Does not gate Pillars A–C.

---

## 19. OCI layer intelligence

**Purpose.** Inventory, diffs, prepare/start time under a **declared** cache condition.

**Prerequisites.** §6; content-addressed blobs; PV-008.

**Before implementing.** Manifest/config/layer descriptors; shared digest ≠ node cache hit; candidate workspace ≠ image layer; report cache/network/runtime or do not claim.

**Learn during.** Registry APIs (Artifact Registry), actual pull timings, what the snapshotter exposes.

**Depends on this.** OCI intelligence milestone only. **Defer:** whiteout reconstruction, lazy loading, Kata, WASI.

---

## 20. LLM Gateway as an optional ModelAccess backend

**Purpose.** Reuse the existing gateway when — and only when — it is evaluation-safe.

**Prerequisites.** §9; the running gateway’s real `/v1/chat/completions` contract.

**Before implementing.** PV-005: no tool-call schema today; cache and fallback default on; no trial/attempt correlation; localhost ≠ GKE. AgentProof must keep `fake` and `direct`.

**Learn during.** The gateway change set (tools, pin-model, cache-off, fallback-off, correlation) as **that** repo’s work; authenticated network path.

**Depends on this.** Optional integration demo. Not the walking skeleton, not investigation, not runtime lab.

---

## 21. Evaluation statistics (enough to not overclaim)

**Purpose.** Honest reports: coverage, missing trials, paired conditions, uncertainty.

**Prerequisites.** Campaign matrix; outcome taxonomy.

**Before implementing.** Task count ≠ repetition count; 5×3 is a demo, not a ranking; error bars and non-success outcomes belong in the report contract.

**Learn during.** How stochastic model noise shows up in the same frozen plan.

**Depends on this.** Published comparisons; investigation conclusions labeled `experimentally_supported`.

---

## Explicitly later (do not study as if they were foundations)

| Topic | When it becomes relevant |
|---|---|
| React investigation UI | After a real timeline exists over evidence APIs |
| Helm, OTel, Prometheus, Grafana | If/when the control plane needs ops telemetry — never as product evidence |
| Warm pools, stargz/Nydus, Kata, WASI | After baseline runtime measurements |
| Recorded-effect replay | After controlled re-execution investigations work |
| Multi-tenant scheduling, SSO | Not in the current architecture |

---

## Suggested learning sequence vs project milestones

| When | Learn in depth | Enough awareness only |
|---|---|---|
| Before first code | §1–4, AD-009 `seq` rules, fixture vs untrusted split | K8s/gVisor vocabulary |
| Fixture E2E (no untrusted code) | §5–8, §12 on the local adapter | Provider tool-call JSON |
| Mediated harness + first fault | §9–11 | Temporal |
| Approved untrusted profile | §13–14, GCP spend/teardown | CRI-O bootstrap |
| Recovery milestone | §15 | OSS agent internals |
| Investigation | §16, §21 | UI frameworks |
| OSS agent | §17 | Gateway tool-call patch |
| Runtime / OCI | §18–19 | Gateway |
| Gateway integration | §20 | — |
