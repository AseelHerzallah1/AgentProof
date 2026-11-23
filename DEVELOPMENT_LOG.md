# Development log

Concise record of completed tasks: what shipped, significant decisions, validation, material issues. No learning essays.

---

### Task 0.1 — Repository skeleton

Date: 2026-11-22 | Commit: phase-0/task-0.1

- Implemented: installable `src/agentproof` package (`__version__ = "0.0.0"`); Hatchling `pyproject.toml`; pytest import smoke test; Ruff; `.gitignore`; `.python-version` (3.11); minimal README; local Git repo. Feature packages (`domain`, `evidence`, …) not created.
- Decision: Python 3.11 venv via `py -3.11` (matches LLM Gateway and PATH `python`; Cursor user default is 3.14). Runtime deps empty until later tasks. `DEVELOPMENT_LOG.md` is tracked (unlike the gateway repo).
- Validation: venv reports `3.11.6`; `pip install -e ".[dev]"` succeeded; `pytest` 1 passed; `ruff check src tests` clean; `import agentproof` prints `0.0.0`. Git author ident: `AseelHerzallah1 <herzalla001@gmail.com>`.
- Issues: none. Default branch after `git init` is `master` (global Git config not changed).

---

### Task 0.2 — Domain types

Date: 2026-11-23 | Commit: phase-0/task-0.2

- Implemented: `agentproof.domain` with UUID4 IDs, `CampaignKind`, `WorkloadClass`, `AttemptState`, `PrimaryOutcome`, and frozen Pydantic `Campaign` / `Trial` / `Attempt`. Attempt validator enforces in-flight vs terminal outcome rules.
- Decision: Pydantic v2 value objects now; SQLAlchemy tables wait for 0.3/0.4. Primary outcome is one enum value; injected faults are not a second primary. `finalized` cannot use branch outcomes. `cleaned` is teardown lifecycle and may retain any primary outcome (cancelled / infrastructure_error / invalid_config included).
- Validation: `pytest` 43 passed; `ruff check src tests` clean.
- Issues: none.

---

### Task 0.3 — Database migrations (version registry)

Date: 2026-11-23 | Commit: phase-0/task-0.3

- Implemented: Alembic + SQLAlchemy 2.0 registry tables `verifier_versions`, `task_versions`, `agent_versions`, `environment_versions`, `runtime_profile_revisions`. ORM rows in `agentproof.db`; Pydantic domain types unchanged.
- Decision: Sync Alembic (no async yet). Portable `Uuid` so tests run on empty SQLite; production URL remains `AGENTPROOF_DATABASE_URL`. No `updated_at`; environment identity is `image_digest` only. Campaign/trial/attempt tables deferred to 0.4.
- Validation: `pytest` 49 passed; `ruff check src tests migrations` clean.
- Issues: none. Live PostgreSQL not required for this task’s acceptance tests.
