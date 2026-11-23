"""Unit tests for Task 0.2 domain types and invariants."""

from uuid import UUID

import pytest
from pydantic import ValidationError

from agentproof.domain import (
    Attempt,
    AttemptState,
    Campaign,
    CampaignKind,
    PrimaryOutcome,
    Trial,
    WorkloadClass,
    new_id,
)


def _trial_kwargs() -> dict:
    return {
        "campaign_id": new_id(),
        "task_version_id": new_id(),
        "agent_version_id": new_id(),
        "environment_version_id": new_id(),
        "runtime_profile_revision_id": new_id(),
        "verifier_version_id": new_id(),
        "repetition_index": 1,
        "workload_class": WorkloadClass.TRUSTED_FIXTURE,
    }


def test_new_id_is_uuid4() -> None:
    value = new_id()
    assert isinstance(value, UUID)
    assert value.version == 4
    assert value != UUID(int=0)


def test_campaign_kinds_are_the_four_architecture_values() -> None:
    assert {kind.value for kind in CampaignKind} == {
        "evaluation",
        "reliability",
        "investigation",
        "runtime",
    }


def test_campaign_rejects_unknown_kind() -> None:
    with pytest.raises(ValidationError):
        Campaign(kind="leaderboard")


def test_trial_is_a_plan_not_an_execution() -> None:
    trial = Trial(**_trial_kwargs())
    assert trial.repetition_index == 1
    assert not hasattr(trial, "primary_outcome")
    assert not hasattr(trial, "attempt_number")
    assert trial.condition_id is None


def test_trial_rejects_non_positive_repetition() -> None:
    with pytest.raises(ValidationError):
        Trial(**{**_trial_kwargs(), "repetition_index": 0})


def test_trial_rejects_nil_campaign_id() -> None:
    with pytest.raises(ValidationError):
        Trial(**{**_trial_kwargs(), "campaign_id": UUID(int=0)})


def test_attempt_starts_in_flight_without_outcome() -> None:
    attempt = Attempt(
        trial_id=new_id(),
        attempt_number=1,
        workload_class=WorkloadClass.TRUSTED_FIXTURE,
    )
    assert attempt.state is AttemptState.CREATED
    assert attempt.primary_outcome is None


def test_infrastructure_retry_is_a_new_attempt_number() -> None:
    trial_id = new_id()
    first = Attempt(
        trial_id=trial_id,
        attempt_number=1,
        workload_class=WorkloadClass.UNTRUSTED_AGENT,
    )
    retry = Attempt(
        trial_id=trial_id,
        attempt_number=2,
        workload_class=WorkloadClass.UNTRUSTED_AGENT,
    )
    assert first.trial_id == retry.trial_id
    assert retry.attempt_number == first.attempt_number + 1
    assert first.id != retry.id


def test_attempt_rejects_non_positive_number() -> None:
    with pytest.raises(ValidationError):
        Attempt(
            trial_id=new_id(),
            attempt_number=0,
            workload_class=WorkloadClass.TRUSTED_FIXTURE,
        )


def test_in_flight_attempt_rejects_primary_outcome() -> None:
    with pytest.raises(ValidationError, match="in-flight"):
        Attempt(
            trial_id=new_id(),
            attempt_number=1,
            workload_class=WorkloadClass.TRUSTED_FIXTURE,
            state=AttemptState.AGENT_RUNNING,
            primary_outcome=PrimaryOutcome.SUCCESS,
        )


def test_terminal_attempt_requires_primary_outcome() -> None:
    with pytest.raises(ValidationError, match="requires a primary_outcome"):
        Attempt(
            trial_id=new_id(),
            attempt_number=1,
            workload_class=WorkloadClass.TRUSTED_FIXTURE,
            state=AttemptState.FINALIZED,
            primary_outcome=None,
        )


@pytest.mark.parametrize(
    ("state", "outcome"),
    [
        (AttemptState.CANCELLED, PrimaryOutcome.CANCELLED),
        (AttemptState.FAILED_INFRASTRUCTURE, PrimaryOutcome.INFRASTRUCTURE_ERROR),
        (AttemptState.FAILED_INVALID_CONFIG, PrimaryOutcome.INVALID_CONFIG),
        (AttemptState.FINALIZED, PrimaryOutcome.SUCCESS),
        (AttemptState.FINALIZED, PrimaryOutcome.AGENT_FAILURE),
        (AttemptState.FINALIZED, PrimaryOutcome.BUDGET_EXCEEDED),
        (AttemptState.FINALIZED, PrimaryOutcome.MODEL_PROVIDER_ERROR),
        (AttemptState.FINALIZED, PrimaryOutcome.UNKNOWN_AMBIGUOUS),
        (AttemptState.CLEANED, PrimaryOutcome.SUCCESS),
        (AttemptState.CLEANED, PrimaryOutcome.CANCELLED),
        (AttemptState.CLEANED, PrimaryOutcome.INFRASTRUCTURE_ERROR),
        (AttemptState.CLEANED, PrimaryOutcome.INVALID_CONFIG),
    ],
)
def test_consistent_terminal_state_and_outcome(
    state: AttemptState, outcome: PrimaryOutcome
) -> None:
    attempt = Attempt(
        trial_id=new_id(),
        attempt_number=1,
        workload_class=WorkloadClass.TRUSTED_FIXTURE,
        state=state,
        primary_outcome=outcome,
    )
    assert attempt.primary_outcome is outcome


@pytest.mark.parametrize(
    ("state", "outcome"),
    [
        (AttemptState.CANCELLED, PrimaryOutcome.SUCCESS),
        (AttemptState.FAILED_INFRASTRUCTURE, PrimaryOutcome.AGENT_FAILURE),
        (AttemptState.FAILED_INVALID_CONFIG, PrimaryOutcome.INFRASTRUCTURE_ERROR),
        (AttemptState.FINALIZED, PrimaryOutcome.CANCELLED),
        (AttemptState.FINALIZED, PrimaryOutcome.INFRASTRUCTURE_ERROR),
        (AttemptState.FINALIZED, PrimaryOutcome.INVALID_CONFIG),
    ],
)
def test_inconsistent_state_and_outcome_rejected(
    state: AttemptState, outcome: PrimaryOutcome
) -> None:
    with pytest.raises(ValidationError):
        Attempt(
            trial_id=new_id(),
            attempt_number=1,
            workload_class=WorkloadClass.TRUSTED_FIXTURE,
            state=state,
            primary_outcome=outcome,
        )


@pytest.mark.parametrize("outcome", list(PrimaryOutcome))
def test_cleaned_preserves_any_primary_outcome(outcome: PrimaryOutcome) -> None:
    """Cleanup is lifecycle; it must not force a different execution outcome."""
    attempt = Attempt(
        trial_id=new_id(),
        attempt_number=1,
        workload_class=WorkloadClass.TRUSTED_FIXTURE,
        state=AttemptState.CLEANED,
        primary_outcome=outcome,
    )
    assert attempt.state is AttemptState.CLEANED
    assert attempt.primary_outcome is outcome


def test_cleaned_still_requires_an_outcome() -> None:
    with pytest.raises(ValidationError, match="requires a primary_outcome"):
        Attempt(
            trial_id=new_id(),
            attempt_number=1,
            workload_class=WorkloadClass.TRUSTED_FIXTURE,
            state=AttemptState.CLEANED,
            primary_outcome=None,
        )


def test_primary_outcome_is_a_single_value_not_a_combination() -> None:
    with pytest.raises(ValidationError):
        Attempt(
            trial_id=new_id(),
            attempt_number=1,
            workload_class=WorkloadClass.TRUSTED_FIXTURE,
            state=AttemptState.FINALIZED,
            primary_outcome=[PrimaryOutcome.SUCCESS, PrimaryOutcome.AGENT_FAILURE],
        )


def test_extra_second_outcome_field_rejected() -> None:
    with pytest.raises(ValidationError):
        Attempt(
            trial_id=new_id(),
            attempt_number=1,
            workload_class=WorkloadClass.TRUSTED_FIXTURE,
            state=AttemptState.FINALIZED,
            primary_outcome=PrimaryOutcome.SUCCESS,
            secondary_outcome=PrimaryOutcome.AGENT_FAILURE,
        )


def test_unknown_workload_class_rejected() -> None:
    with pytest.raises(ValidationError):
        Attempt(
            trial_id=new_id(),
            attempt_number=1,
            workload_class="local_docker",
        )


def test_models_are_frozen() -> None:
    campaign = Campaign(kind=CampaignKind.EVALUATION)
    with pytest.raises(ValidationError):
        campaign.kind = CampaignKind.RUNTIME  # type: ignore[misc]
