# AgentProof

Reliability and execution intelligence platform for AI agents.

This repository is in early construction. Planning documents live in `docs/`. Nothing beyond the package skeleton is implemented yet.

## Requirements

- Python **3.11** (this workspace is pinned in `.python-version`)

## Setup

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -c "import sys; print(sys.version)"   # expect 3.11.x
pip install -e ".[dev]"
```

## Tests

```powershell
pytest
ruff check src tests
```
