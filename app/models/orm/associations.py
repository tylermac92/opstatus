from sqlalchemy import Column, ForeignKey, Table

from app.models.orm.base import Base

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
