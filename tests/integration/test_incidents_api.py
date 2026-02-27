import pytest
from httpx import AsyncClient

# --- helpers ---


async def create_service(client: AsyncClient, name: str) -> str:
    response = await client.post("/api/v1/services", json={"name": name})
    assert response.status_code == 201
    return str(response.json()["id"])


async def create_incident(
    client: AsyncClient,
    service_id: str,
    title: str = "Test Incident",
    severity: str = "high",
) -> str:
    response = await client.post(
        "/api/v1/incidents",
        json={
            "title": title,
            "severity": severity,
            "service_ids": [service_id],
        },
    )
    assert response.status_code == 201
    return str(response.json()["id"])


# --- list incidents ---


@pytest.mark.asyncio
async def test_list_incidents_empty(client: AsyncClient) -> None:
    response = await client.get("/api/v1/incidents")
    assert response.status_code == 200
    body = response.json()
    assert body["data"] == []
    assert body["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_list_incidents_returns_all(client: AsyncClient) -> None:
    service_id = await create_service(client, "List Test Service")
    await create_incident(client, service_id, title="First")
    await create_incident(client, service_id, title="Second")

    response = await client.get("/api/v1/incidents")
    assert response.status_code == 200
    assert response.json()["meta"]["total"] == 2


@pytest.mark.asyncio
async def test_list_incidents_ordered_newest_first(client: AsyncClient) -> None:
    service_id = await create_service(client, "Order Test Service")
    await create_incident(client, service_id, title="First")
    await create_incident(client, service_id, title="Second")

    response = await client.get("/api/v1/incidents")
    titles = [i["title"] for i in response.json()["data"]]
    assert titles[0] == "Second"
    assert titles[1] == "First"


@pytest.mark.asyncio
async def test_list_incidents_filter_by_status(client: AsyncClient) -> None:
    service_id = await create_service(client, "Filter Status Service")
    await create_incident(client, service_id, title="Active")
    incident_id = await create_incident(client, service_id, title="To Resolve")
    await client.post(f"/api/v1/incidents/{incident_id}/resolve")

    response = await client.get("/api/v1/incidents?status=investigating")
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["title"] == "Active"


@pytest.mark.asyncio
async def test_list_incidents_filter_by_severity(client: AsyncClient) -> None:
    service_id = await create_service(client, "Filter Severity Service")
    await create_incident(client, service_id, title="High", severity="high")
    await create_incident(client, service_id, title="Low", severity="low")

    response = await client.get("/api/v1/incidents?severity=high")
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["title"] == "High"


@pytest.mark.asyncio
async def test_list_incidents_filter_by_service_id(client: AsyncClient) -> None:
    service_a = await create_service(client, "Service A")
    service_b = await create_service(client, "Service B")
    await create_incident(client, service_a, title="A's Incident")
    await create_incident(client, service_b, title="B's Incident")

    response = await client.get(f"/api/v1/incidents?service_id={service_a}")
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["title"] == "A's Incident"


@pytest.mark.asyncio
async def test_list_incidents_combined_filters(client: AsyncClient) -> None:
    service_id = await create_service(client, "Combined Filter Service")
    await create_incident(client, service_id, title="High Active", severity="high")
    await create_incident(client, service_id, title="Low Active", severity="low")

    response = await client.get("/api/v1/incidents?severity=high&status=investigating")
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["title"] == "High Active"


# --- create incident ---


@pytest.mark.asyncio
async def test_create_incident_success(client: AsyncClient) -> None:
    service_id = await create_service(client, "Create Test Service")
    response = await client.post(
        "/api/v1/incidents",
        json={
            "title": "New Incident",
            "severity": "critical",
            "service_ids": [service_id],
            "body": "Something is very wrong.",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "New Incident"
    assert body["severity"] == "critical"
    assert body["status"] == "investigating"
    assert body["body"] == "Something is very wrong."
    assert service_id in body["service_ids"]


@pytest.mark.asyncio
async def test_create_incident_initial_status_is_investigating(
    client: AsyncClient,
) -> None:
    service_id = await create_service(client, "Status Test Service")
    incident_id = await create_incident(client, service_id)

    response = await client.get(f"/api/v1/incidents/{incident_id}")
    assert response.json()["status"] == "investigating"


@pytest.mark.asyncio
async def test_create_incident_updates_service_status_to_outage(
    client: AsyncClient,
) -> None:
    service_id = await create_service(client, "Outage Test Service")
    await create_incident(client, service_id, severity="critical")

    response = await client.get(f"/api/v1/services/{service_id}")
    assert response.json()["status"] == "outage"


@pytest.mark.asyncio
async def test_create_incident_high_severity_sets_outage(
    client: AsyncClient,
) -> None:
    service_id = await create_service(client, "High Severity Service")
    await create_incident(client, service_id, severity="high")

    response = await client.get(f"/api/v1/services/{service_id}")
    assert response.json()["status"] == "outage"


@pytest.mark.asyncio
async def test_create_incident_low_severity_sets_degraded(
    client: AsyncClient,
) -> None:
    service_id = await create_service(client, "Degraded Service")
    await create_incident(client, service_id, severity="low")

    response = await client.get(f"/api/v1/services/{service_id}")
    assert response.json()["status"] == "degraded"


@pytest.mark.asyncio
async def test_create_incident_invalid_service_id_returns_404(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/incidents",
        json={
            "title": "Ghost Incident",
            "severity": "low",
            "service_ids": ["00000000-0000-0000-0000-000000000000"],
        },
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_create_incident_missing_fields_returns_422(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/incidents",
        json={"title": "Missing fields"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_create_incident_empty_service_ids_returns_422(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/incidents",
        json={"title": "Test", "severity": "low", "service_ids": []},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


# --- get incident by ID ---


@pytest.mark.asyncio
async def test_get_incident_by_id_success(client: AsyncClient) -> None:
    service_id = await create_service(client, "Get Test Service")
    incident_id = await create_incident(client, service_id)

    response = await client.get(f"/api/v1/incidents/{incident_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == incident_id
    assert "updates" in body


@pytest.mark.asyncio
async def test_get_incident_includes_empty_updates_array(
    client: AsyncClient,
) -> None:
    service_id = await create_service(client, "Updates Test Service")
    incident_id = await create_incident(client, service_id)

    response = await client.get(f"/api/v1/incidents/{incident_id}")
    assert response.json()["updates"] == []


@pytest.mark.asyncio
async def test_get_incident_not_found_returns_404(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/incidents/00000000-0000-0000-0000-000000000000"
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_get_incident_invalid_uuid_returns_422(client: AsyncClient) -> None:
    response = await client.get("/api/v1/incidents/not-a-uuid")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


# --- update incident ---


@pytest.mark.asyncio
async def test_update_incident_title(client: AsyncClient) -> None:
    service_id = await create_service(client, "Update Title Service")
    incident_id = await create_incident(client, service_id)

    response = await client.patch(
        f"/api/v1/incidents/{incident_id}",
        json={"title": "Updated Title"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"


@pytest.mark.asyncio
async def test_update_incident_valid_status_transition(
    client: AsyncClient,
) -> None:
    service_id = await create_service(client, "Transition Service")
    incident_id = await create_incident(client, service_id)

    response = await client.patch(
        f"/api/v1/incidents/{incident_id}",
        json={"status": "identified"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "identified"


@pytest.mark.asyncio
async def test_update_incident_invalid_status_transition_returns_409(
    client: AsyncClient,
) -> None:
    service_id = await create_service(client, "Invalid Transition Service")
    incident_id = await create_incident(client, service_id)

    response = await client.patch(
        f"/api/v1/incidents/{incident_id}",
        json={"status": "monitoring"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_update_incident_severity_affects_service_status(
    client: AsyncClient,
) -> None:
    service_id = await create_service(client, "Severity Change Service")
    incident_id = await create_incident(client, service_id, severity="low")

    service_response = await client.get(f"/api/v1/services/{service_id}")
    assert service_response.json()["status"] == "degraded"

    await client.patch(
        f"/api/v1/incidents/{incident_id}",
        json={"severity": "critical"},
    )

    service_response = await client.get(f"/api/v1/services/{service_id}")
    assert service_response.json()["status"] == "outage"


@pytest.mark.asyncio
async def test_update_incident_not_found_returns_404(client: AsyncClient) -> None:
    response = await client.patch(
        "/api/v1/incidents/00000000-0000-0000-0000-000000000000",
        json={"title": "Ghost"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


# --- append incident update ---


@pytest.mark.asyncio
async def test_append_incident_update_success(client: AsyncClient) -> None:
    service_id = await create_service(client, "Append Update Service")
    incident_id = await create_incident(client, service_id)

    response = await client.post(
        f"/api/v1/incidents/{incident_id}/updates",
        json={"message": "Working on it.", "status": "investigating"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["message"] == "Working on it."
    assert body["status"] == "investigating"
    assert body["incident_id"] == incident_id


@pytest.mark.asyncio
async def test_append_incident_update_appears_in_timeline(
    client: AsyncClient,
) -> None:
    service_id = await create_service(client, "Timeline Service")
    incident_id = await create_incident(client, service_id)

    await client.post(
        f"/api/v1/incidents/{incident_id}/updates",
        json={"message": "First update.", "status": "investigating"},
    )
    await client.post(
        f"/api/v1/incidents/{incident_id}/updates",
        json={"message": "Second update.", "status": "investigating"},
    )

    response = await client.get(f"/api/v1/incidents/{incident_id}")
    updates = response.json()["updates"]
    assert len(updates) == 2
    assert updates[0]["message"] == "First update."
    assert updates[1]["message"] == "Second update."


@pytest.mark.asyncio
async def test_append_update_timeline_is_ordered_ascending(
    client: AsyncClient,
) -> None:
    service_id = await create_service(client, "Order Service")
    incident_id = await create_incident(client, service_id)

    for i in range(3):
        await client.post(
            f"/api/v1/incidents/{incident_id}/updates",
            json={"message": f"Update {i}", "status": "investigating"},
        )

    response = await client.get(f"/api/v1/incidents/{incident_id}")
    updates = response.json()["updates"]
    created_ats = [u["created_at"] for u in updates]
    assert created_ats == sorted(created_ats)


@pytest.mark.asyncio
async def test_append_update_to_resolved_incident_returns_409(
    client: AsyncClient,
) -> None:
    service_id = await create_service(client, "Resolved Service")
    incident_id = await create_incident(client, service_id)
    await client.post(f"/api/v1/incidents/{incident_id}/resolve")

    response = await client.post(
        f"/api/v1/incidents/{incident_id}/updates",
        json={"message": "Too late.", "status": "resolved"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_append_update_to_nonexistent_incident_returns_404(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/incidents/00000000-0000-0000-0000-000000000000/updates",
        json={"message": "Ghost update.", "status": "investigating"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


# --- resolve incident ---


@pytest.mark.asyncio
async def test_resolve_incident_success(client: AsyncClient) -> None:
    service_id = await create_service(client, "Resolve Test Service")
    incident_id = await create_incident(client, service_id)

    response = await client.post(f"/api/v1/incidents/{incident_id}/resolve")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "resolved"
    assert body["resolved_at"] is not None


@pytest.mark.asyncio
async def test_resolve_incident_appends_final_update(
    client: AsyncClient,
) -> None:
    service_id = await create_service(client, "Final Update Service")
    incident_id = await create_incident(client, service_id)

    response = await client.post(f"/api/v1/incidents/{incident_id}/resolve")
    updates = response.json()["updates"]
    assert len(updates) == 1
    assert updates[0]["message"] == "Incident resolved."
    assert updates[0]["status"] == "resolved"


@pytest.mark.asyncio
async def test_resolve_incident_restores_service_to_operational(
    client: AsyncClient,
) -> None:
    service_id = await create_service(client, "Recovery Service")
    incident_id = await create_incident(client, service_id, severity="critical")

    service_response = await client.get(f"/api/v1/services/{service_id}")
    assert service_response.json()["status"] == "outage"

    await client.post(f"/api/v1/incidents/{incident_id}/resolve")

    service_response = await client.get(f"/api/v1/services/{service_id}")
    assert service_response.json()["status"] == "operational"


@pytest.mark.asyncio
async def test_resolve_already_resolved_incident_returns_409(
    client: AsyncClient,
) -> None:
    service_id = await create_service(client, "Double Resolve Service")
    incident_id = await create_incident(client, service_id)
    await client.post(f"/api/v1/incidents/{incident_id}/resolve")

    response = await client.post(f"/api/v1/incidents/{incident_id}/resolve")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_resolve_nonexistent_incident_returns_404(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/incidents/00000000-0000-0000-0000-000000000000/resolve"
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


# --- service status derivation from incidents ---


@pytest.mark.asyncio
async def test_service_status_with_multiple_incidents(
    client: AsyncClient,
) -> None:
    service_id = await create_service(client, "Multi Incident Service")
    low_id = await create_incident(client, service_id, severity="low")
    await create_incident(client, service_id, severity="critical")

    service_response = await client.get(f"/api/v1/services/{service_id}")
    assert service_response.json()["status"] == "outage"

    await client.post(f"/api/v1/incidents/{low_id}/resolve")
    service_response = await client.get(f"/api/v1/services/{service_id}")
    assert service_response.json()["status"] == "outage"


@pytest.mark.asyncio
async def test_service_returns_to_degraded_after_critical_resolved(
    client: AsyncClient,
) -> None:
    service_id = await create_service(client, "Partial Recovery Service")
    critical_id = await create_incident(client, service_id, severity="critical")
    await create_incident(client, service_id, severity="low")

    await client.post(f"/api/v1/incidents/{critical_id}/resolve")

    service_response = await client.get(f"/api/v1/services/{service_id}")
    assert service_response.json()["status"] == "degraded"
