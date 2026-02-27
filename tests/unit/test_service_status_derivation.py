from app.models.enums import IncidentSeverity, IncidentStatus
from app.models.orm.incident import Incident
from app.services.services import derive_service_status


def make_incident(
    severity: IncidentSeverity,
    status: IncidentStatus = IncidentStatus.investigating,
) -> Incident:
    # Construct a bare ORM instance without a database session.
    # Only severity and status are set; derive_service_status inspects nothing else.
    incident = Incident()
    incident.severity = severity
    incident.status = status
    return incident


# --- operational ---


def test_no_incidents_returns_operational() -> None:
    assert derive_service_status([]) == "operational"


def test_only_resolved_incidents_returns_operational() -> None:
    incidents = [
        make_incident(IncidentSeverity.critical, IncidentStatus.resolved),
        make_incident(IncidentSeverity.high, IncidentStatus.resolved),
    ]
    assert derive_service_status(incidents) == "operational"


# --- outage ---


def test_critical_incident_returns_outage() -> None:
    incidents = [make_incident(IncidentSeverity.critical)]
    assert derive_service_status(incidents) == "outage"


def test_high_incident_returns_outage() -> None:
    incidents = [make_incident(IncidentSeverity.high)]
    assert derive_service_status(incidents) == "outage"


def test_mixed_severities_with_critical_returns_outage() -> None:
    incidents = [
        make_incident(IncidentSeverity.critical),
        make_incident(IncidentSeverity.low),
    ]
    assert derive_service_status(incidents) == "outage"


def test_mixed_severities_with_high_returns_outage() -> None:
    incidents = [
        make_incident(IncidentSeverity.high),
        make_incident(IncidentSeverity.medium),
    ]
    assert derive_service_status(incidents) == "outage"


# --- degraded ---


def test_medium_incident_returns_degraded() -> None:
    incidents = [make_incident(IncidentSeverity.medium)]
    assert derive_service_status(incidents) == "degraded"


def test_low_incident_returns_degraded() -> None:
    incidents = [make_incident(IncidentSeverity.low)]
    assert derive_service_status(incidents) == "degraded"


def test_multiple_low_and_medium_incidents_returns_degraded() -> None:
    incidents = [
        make_incident(IncidentSeverity.medium),
        make_incident(IncidentSeverity.low),
    ]
    assert derive_service_status(incidents) == "degraded"


# --- resolved incidents excluded ---


def test_resolved_critical_with_active_low_returns_degraded() -> None:
    incidents = [
        make_incident(IncidentSeverity.critical, IncidentStatus.resolved),
        make_incident(IncidentSeverity.low, IncidentStatus.investigating),
    ]
    assert derive_service_status(incidents) == "degraded"


def test_resolved_high_with_no_other_active_returns_operational() -> None:
    incidents = [
        make_incident(IncidentSeverity.high, IncidentStatus.resolved),
    ]
    assert derive_service_status(incidents) == "operational"


# --- precedence ---


def test_critical_takes_precedence_over_low() -> None:
    incidents = [
        make_incident(IncidentSeverity.low),
        make_incident(IncidentSeverity.critical),
    ]
    assert derive_service_status(incidents) == "outage"


def test_high_takes_precedence_over_medium() -> None:
    incidents = [
        make_incident(IncidentSeverity.medium),
        make_incident(IncidentSeverity.high),
    ]
    assert derive_service_status(incidents) == "outage"
