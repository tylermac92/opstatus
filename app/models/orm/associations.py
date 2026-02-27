from sqlalchemy import Column, ForeignKey, Table

from app.models.orm.base import Base

# Pure join table for the many-to-many relationship between services and incidents.
# CASCADE on both foreign keys means rows are automatically removed when either
# the parent service or the parent incident is deleted.
service_incidents = Table(
    "service_incidents",
    Base.metadata,
    Column(
        "service_id",
        ForeignKey("services.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "incident_id",
        ForeignKey("incidents.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)
