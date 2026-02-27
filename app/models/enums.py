import enum

# StrEnum members compare equal to their string value, so enum instances can be
# used directly in SQLAlchemy queries and JSON responses without extra conversion.


# Derived at read time from active incident severity; never stored in the database.
class ServiceStatus(enum.StrEnum):
    operational = "operational"
    degraded = "degraded"
    outage = "outage"


class IncidentSeverity(enum.StrEnum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


# Members are ordered to reflect the incident lifecycle.
# Lifecycle order: investigating → identified → monitoring → resolved.
# Only forward transitions are allowed; "resolved" is terminal.
# "resolved" is a terminal state; no further transitions are allowed.
class IncidentStatus(enum.StrEnum):
    investigating = "investigating"
    identified = "identified"
    monitoring = "monitoring"
    resolved = "resolved"
