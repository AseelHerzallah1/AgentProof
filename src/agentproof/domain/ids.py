"""Stable identifier helpers. IDs are UUID4 values (AD-002 / architecture)."""

from uuid import UUID, uuid4


def new_id() -> UUID:
    """Return a new UUID4. Nil UUID is not used as an identity."""
    return uuid4()
