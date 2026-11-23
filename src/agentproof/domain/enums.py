"""Closed vocabularies for campaigns, workloads, attempt lifecycle, and outcomes."""

from enum import StrEnum


class CampaignKind(StrEnum):
    """Typed campaigns share one trial/attempt substrate (AD-005)."""

    EVALUATION = "evaluation"
    RELIABILITY = "reliability"
    INVESTIGATION = "investigation"
    RUNTIME = "runtime"


class WorkloadClass(StrEnum):
    """What may run on a given sandbox profile (AD-006)."""

    TRUSTED_FIXTURE = "trusted_fixture"
    UNTRUSTED_AGENT = "untrusted_agent"


class AttemptState(StrEnum):
    """Coordinator v1 states (ARCHITECTURE §9.2)."""

    CREATED = "created"
    ADMITTED = "admitted"
    SANDBOX_ALLOCATED = "sandbox_allocated"
    AGENT_RUNNING = "agent_running"
    EXPORTED = "exported"
    VERIFYING = "verifying"
    FINALIZED = "finalized"
    CLEANED = "cleaned"
    CANCELLED = "cancelled"
    FAILED_INFRASTRUCTURE = "failed_infrastructure"
    FAILED_INVALID_CONFIG = "failed_invalid_config"


class PrimaryOutcome(StrEnum):
    """Mutually exclusive attempt result (AD-011). Faults are events, not a second primary."""

    SUCCESS = "success"
    AGENT_FAILURE = "agent_failure"
    BUDGET_EXCEEDED = "budget_exceeded"
    MODEL_PROVIDER_ERROR = "model_provider_error"
    INFRASTRUCTURE_ERROR = "infrastructure_error"
    INVALID_CONFIG = "invalid_config"
    CANCELLED = "cancelled"
    UNKNOWN_AMBIGUOUS = "unknown_ambiguous"
