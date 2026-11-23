"""Immutable version-registry rows (ARCHITECTURE §10). No updated_at."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from agentproof.db.base import Base


class VerifierVersionRow(Base):
    """Hidden-check identity. Check payloads are not stored on this row."""

    __tablename__ = "verifier_versions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)


class TaskVersionRow(Base):
    __tablename__ = "task_versions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    verifier_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("verifier_versions.id"),
        nullable=False,
    )


class AgentVersionRow(Base):
    __tablename__ = "agent_versions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    adapter_name: Mapped[str] = mapped_column(String(255), nullable=False)


class EnvironmentVersionRow(Base):
    """Identity is an image digest, never a moving tag."""

    __tablename__ = "environment_versions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    image_digest: Mapped[str] = mapped_column(String(255), nullable=False)
    platform: Mapped[str] = mapped_column(String(64), nullable=False)


class RuntimeProfileRevisionRow(Base):
    __tablename__ = "runtime_profile_revisions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    isolation_class: Mapped[str] = mapped_column(String(64), nullable=False)
