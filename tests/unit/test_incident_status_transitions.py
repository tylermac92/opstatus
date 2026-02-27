import pytest

from app.core.exceptions import ConflictError
from app.models.enums import IncidentStatus
from app.services.incidents import validate_status_transition

# --- valid transitions ---


def test_investigating_to_identified_is_valid() -> None:
    validate_status_transition(IncidentStatus.investigating, IncidentStatus.identified)


def test_identified_to_monitoring_is_valid() -> None:
    validate_status_transition(IncidentStatus.identified, IncidentStatus.monitoring)


def test_monitoring_to_resolved_is_valid() -> None:
    validate_status_transition(IncidentStatus.monitoring, IncidentStatus.resolved)


# --- invalid transitions ---


def test_monitoring_to_investigating_raises_conflict() -> None:
    with pytest.raises(ConflictError):
        validate_status_transition(
            IncidentStatus.monitoring, IncidentStatus.investigating
        )


def test_monitoring_to_identified_raises_conflict() -> None:
    with pytest.raises(ConflictError):
        validate_status_transition(IncidentStatus.monitoring, IncidentStatus.identified)


def test_investigating_to_monitoring_raises_conflict() -> None:
    with pytest.raises(ConflictError):
        validate_status_transition(
            IncidentStatus.investigating, IncidentStatus.monitoring
        )


def test_investigating_to_resolved_raises_conflict() -> None:
    with pytest.raises(ConflictError):
        validate_status_transition(
            IncidentStatus.investigating, IncidentStatus.resolved
        )


def test_identified_to_investigating_raises_conflict() -> None:
    with pytest.raises(ConflictError):
        validate_status_transition(
            IncidentStatus.identified, IncidentStatus.investigating
        )


def test_identified_to_resolved_raises_conflict() -> None:
    with pytest.raises(ConflictError):
        validate_status_transition(IncidentStatus.identified, IncidentStatus.resolved)


# --- resolved is a terminal state ---


def test_resolved_to_investigating_raises_conflict() -> None:
    with pytest.raises(ConflictError):
        validate_status_transition(
            IncidentStatus.resolved, IncidentStatus.investigating
        )


def test_resolved_to_identified_raises_conflict() -> None:
    with pytest.raises(ConflictError):
        validate_status_transition(IncidentStatus.resolved, IncidentStatus.identified)


def test_resolved_to_monitoring_raises_conflict() -> None:
    with pytest.raises(ConflictError):
        validate_status_transition(IncidentStatus.resolved, IncidentStatus.monitoring)


def test_resolved_to_resolved_raises_conflict() -> None:
    with pytest.raises(ConflictError):
        validate_status_transition(IncidentStatus.resolved, IncidentStatus.resolved)


# --- error message quality ---


def test_conflict_error_message_names_current_status() -> None:
    with pytest.raises(ConflictError) as exc_info:
        validate_status_transition(
            IncidentStatus.monitoring, IncidentStatus.investigating
        )
    assert "monitoring" in exc_info.value.message


def test_conflict_error_message_names_target_status() -> None:
    with pytest.raises(ConflictError) as exc_info:
        validate_status_transition(
            IncidentStatus.monitoring, IncidentStatus.investigating
        )
    assert "investigating" in exc_info.value.message


# --- already resolved incident ---


def test_already_resolved_incident_cannot_transition_to_any_state() -> None:
    for target in IncidentStatus:
        with pytest.raises(ConflictError):
            validate_status_transition(IncidentStatus.resolved, target)
