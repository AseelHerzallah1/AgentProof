# Development log

Concise record of completed tasks: what shipped, significant decisions, validation, material issues. No learning essays.

---

### Task 0.1 — Repository skeleton

Date: 2026-11-22 | Commit: phase-0/task-0.1

- Implemented: installable `src/agentproof` package (`__version__ = "0.0.0"`); Hatchling `pyproject.toml`; pytest import smoke test; Ruff; `.gitignore`; `.python-version` (3.11); minimal README; local Git repo. Feature packages (`domain`, `evidence`, …) not created.
- Decision: Python 3.11 venv via `py -3.11` (matches LLM Gateway and PATH `python`; Cursor user default is 3.14). Runtime deps empty until later tasks. `DEVELOPMENT_LOG.md` is tracked (unlike the gateway repo).
- Validation: venv reports `3.11.6`; `pip install -e ".[dev]"` succeeded; `pytest` 1 passed; `ruff check src tests` clean; `import agentproof` prints `0.0.0`. Git author ident: `AseelHerzallah1 <herzalla001@gmail.com>`.
- Issues: none. Default branch after `git init` is `master` (global Git config not changed).
