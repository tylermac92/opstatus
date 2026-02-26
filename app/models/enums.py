import enum


class ServiceStatus(enum.StrEnum):
    operational = "operational"
    degraded = "degraded"
    outage = "outage"


class IncidentSeverity(enum.StrEnum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class IncidentStatus(enum.StrEnum):
    investigating = "investigating"
    identified = "identified"
    monitoring = "monitoring"
    resolved = "resolved"
