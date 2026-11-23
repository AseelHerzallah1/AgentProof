"""In-memory domain types. Persistence belongs to later tasks."""

from agentproof.domain.enums import (
    AttemptState,
    CampaignKind,
    PrimaryOutcome,
    WorkloadClass,
)
from agentproof.domain.ids import new_id
from agentproof.domain.models import Attempt, Campaign, Trial

__all__ = [
    "Attempt",
    "AttemptState",
    "Campaign",
    "CampaignKind",
    "PrimaryOutcome",
    "Trial",
    "WorkloadClass",
    "new_id",
]
