"""Alembic upgrade/downgrade of the immutable version registry on an empty DB."""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_TABLES = {
    "verifier_versions",
    "task_versions",
    "agent_versions",
    "environment_versions",
    "runtime_profile_revisions",
}


def _alembic_config(url: str) -> Config:
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "migrations"))
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


def _table_names(url: str) -> set[str]:
    engine = create_engine(url)
    try:
        return set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def _columns(url: str, table: str) -> set[str]:
    engine = create_engine(url)
    try:
        return {column["name"] for column in inspect(engine).get_columns(table)}
    finally:
        engine.dispose()


def test_upgrade_creates_registry_tables(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'empty.db'}"
    command.upgrade(_alembic_config(url), "head")
    names = _table_names(url)
    assert REGISTRY_TABLES <= names
    assert "campaigns" not in names
    assert "trials" not in names
    assert "attempts" not in names


def test_downgrade_drops_registry_tables(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'empty.db'}"
    cfg = _alembic_config(url)
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "base")
    names = _table_names(url)
    assert names.isdisjoint(REGISTRY_TABLES)


def test_upgrade_after_downgrade_restores_tables(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'empty.db'}"
    cfg = _alembic_config(url)
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    assert REGISTRY_TABLES <= _table_names(url)


def test_environment_identity_is_digest_not_tag(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'empty.db'}"
    command.upgrade(_alembic_config(url), "head")
    columns = _columns(url, "environment_versions")
    assert "image_digest" in columns
    assert "image_tag" not in columns


def test_version_tables_have_no_updated_at(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'empty.db'}"
    command.upgrade(_alembic_config(url), "head")
    for table in REGISTRY_TABLES:
        assert "updated_at" not in _columns(url, table)
        assert "created_at" in _columns(url, table)


def test_task_version_requires_verifier(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'empty.db'}"
    command.upgrade(_alembic_config(url), "head")
    engine = create_engine(url)
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys = ON"))
        conn.commit()
        with pytest.raises(Exception, match="FOREIGN KEY|foreign key"):
            conn.execute(
                text(
                    "INSERT INTO task_versions "
                    "(id, objective, verifier_version_id) "
                    "VALUES ('00000000-0000-4000-8000-000000000001', 'x', "
                    "'00000000-0000-4000-8000-000000000002')"
                )
            )
            conn.commit()
    engine.dispose()
