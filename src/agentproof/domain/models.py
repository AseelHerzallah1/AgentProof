"""Value objects for campaigns, planned trials, and concrete attempts."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from agentproof.domain.enums import AttemptState, CampaignKind, PrimaryOutcome, WorkloadClass
from agentproof.domain.ids import new_id

_IN_FLIGHT_STATES = frozenset(
    {
        AttemptState.CREATED,
        AttemptState.ADMITTED,
        AttemptState.SANDBOX_ALLOCATED,
        AttemptState.AGENT_RUNNING,
        AttemptState.EXPORTED,
        AttemptState.VERIFYING,
    }
)

_TERMINAL_STATES = frozenset(
    {
        AttemptState.FINALIZED,
        AttemptState.CLEANED,
        AttemptState.CANCELLED,
        AttemptState.FAILED_INFRASTRUCTURE,
        AttemptState.FAILED_INVALID_CONFIG,
    }
)

_FINALIZED_OUTCOMES = frozenset(
    {
        PrimaryOutcome.SUCCESS,
        PrimaryOutcome.AGENT_FAILURE,
        PrimaryOutcome.BUDGET_EXCEEDED,
        PrimaryOutcome.MODEL_PROVIDER_ERROR,
        PrimaryOutcome.UNKNOWN_AMBIGUOUS,
    }
)

_NIL_UUID = UUID(int=0)


def _reject_nil_uuid(value: UUID) -> UUID:
    if value == _NIL_UUID:
        msg = "identity must not be the nil UUID"
        raise ValueError(msg)
    return value


class Campaign(BaseModel):
    """Registered comparison or investigation design. Plan expansion is a later task."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID = Field(default_factory=new_id)
    kind: CampaignKind

    @field_validator("id")
    @classmethod
    def _id_not_nil(cls, value: UUID) -> UUID:
        return _reject_nil_uuid(value)


class Trial(BaseModel):
    """One planned combination of versions, optional condition, profile, and repetition.

    A trial is not an execution. Infrastructure retries do not mutate a trial; they
    create new attempts of the same trial.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID = Field(default_factory=new_id)
    campaign_id: UUID
    task_version_id: UUID
    agent_version_id: UUID
    environment_version_id: UUID
    runtime_profile_revision_id: UUID
    verifier_version_id: UUID
    repetition_index: int = Field(ge=1)
    workload_class: WorkloadClass
    condition_id: UUID | None = None

    @field_validator(
        "id",
        "campaign_id",
        "task_version_id",
        "agent_version_id",
        "environment_version_id",
        "runtime_profile_revision_id",
        "verifier_version_id",
    )
    @classmethod
    def _id_not_nil(cls, value: UUID) -> UUID:
        return _reject_nil_uuid(value)


class Attempt(BaseModel):
    """One concrete execution of a trial.

    Primary outcome is the execution result. ``cleaned`` is lifecycle after
    teardown and may follow any terminal branch without changing that outcome.
    Secondary contributing events are not stored here.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID = Field(default_factory=new_id)
    trial_id: UUID
    attempt_number: int = Field(ge=1)
    workload_class: WorkloadClass
    state: AttemptState = AttemptState.CREATED
    primary_outcome: PrimaryOutcome | None = None

    @field_validator("id", "trial_id")
    @classmethod
    def _id_not_nil(cls, value: UUID) -> UUID:
        return _reject_nil_uuid(value)

    @model_validator(mode="after")
    def _outcome_matches_state(self) -> Attempt:
        if self.state in _IN_FLIGHT_STATES:
            if self.primary_outcome is not None:
                msg = f"in-flight state {self.state} must not have a primary_outcome"
                raise ValueError(msg)
            return self

        if self.state not in _TERMINAL_STATES:
            msg = f"unrecognized attempt state {self.state}"
            raise ValueError(msg)

        if self.primary_outcome is None:
            msg = f"terminal state {self.state} requires a primary_outcome"
            raise ValueError(msg)

        cancelled_ok = self.primary_outcome == PrimaryOutcome.CANCELLED
        if self.state == AttemptState.CANCELLED and not cancelled_ok:
            msg = "cancelled state requires primary_outcome=cancelled"
            raise ValueError(msg)
        if (
            self.state == AttemptState.FAILED_INFRASTRUCTURE
            and self.primary_outcome != PrimaryOutcome.INFRASTRUCTURE_ERROR
        ):
            msg = "failed_infrastructure requires primary_outcome=infrastructure_error"
            raise ValueError(msg)
        if (
            self.state == AttemptState.FAILED_INVALID_CONFIG
            and self.primary_outcome != PrimaryOutcome.INVALID_CONFIG
        ):
            msg = "failed_invalid_config requires primary_outcome=invalid_config"
            raise ValueError(msg)
        finalized_ok = self.primary_outcome in _FINALIZED_OUTCOMES
        if self.state == AttemptState.FINALIZED and not finalized_ok:
            msg = (
                f"state {self.state} cannot have primary_outcome="
                f"{self.primary_outcome}; use the matching terminal branch"
            )
            raise ValueError(msg)
        return self
