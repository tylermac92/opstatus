import pytest
from httpx import AsyncClient

# --- list services ---


@pytest.mark.asyncio
async def test_list_services_empty(client: AsyncClient) -> None:
    response = await client.get("/api/v1/services")
    assert response.status_code == 200
    body = response.json()
    assert body["data"] == []
    assert body["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_list_services_returns_all(client: AsyncClient) -> None:
    await client.post("/api/v1/services", json={"name": "Service A"})
    await client.post("/api/v1/services", json={"name": "Service B"})

    response = await client.get("/api/v1/services")
    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["total"] == 2
    names = [s["name"] for s in body["data"]]
    assert "Service A" in names
    assert "Service B" in names


@pytest.mark.asyncio
async def test_list_services_response_shape(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/services",
        json={"name": "Shape Test", "description": "A description"},
    )
    response = await client.get("/api/v1/services")
    service = response.json()["data"][0]
    assert "id" in service
    assert "name" in service
    assert "description" in service
    assert "status" in service
    assert "created_at" in service
    assert "updated_at" in service


@pytest.mark.asyncio
async def test_list_services_new_service_is_operational(client: AsyncClient) -> None:
    await client.post("/api/v1/services", json={"name": "New Service"})
    response = await client.get("/api/v1/services")
    service = response.json()["data"][0]
    assert service["status"] == "operational"


# --- create service ---


@pytest.mark.asyncio
async def test_create_service_success(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/services",
        json={"name": "Payment Service", "description": "Handles payments"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Payment Service"
    assert body["description"] == "Handles payments"
    assert body["status"] == "operational"
    assert "id" in body


@pytest.mark.asyncio
async def test_create_service_without_description(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/services",
        json={"name": "Minimal Service"},
    )
    assert response.status_code == 201
    assert response.json()["description"] is None


@pytest.mark.asyncio
async def test_create_service_duplicate_name_returns_409(client: AsyncClient) -> None:
    await client.post("/api/v1/services", json={"name": "Duplicate"})
    response = await client.post("/api/v1/services", json={"name": "Duplicate"})
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_create_service_missing_name_returns_422(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/services",
        json={"description": "No name"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_create_service_blank_name_returns_422(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/services",
        json={"name": ""},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_create_service_trims_whitespace(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/services",
        json={"name": "  Trimmed  "},
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Trimmed"


# --- get service by ID ---


@pytest.mark.asyncio
async def test_get_service_by_id_success(client: AsyncClient) -> None:
    created = await client.post(
        "/api/v1/services",
        json={"name": "Fetch Me"},
    )
    service_id = created.json()["id"]

    response = await client.get(f"/api/v1/services/{service_id}")
    assert response.status_code == 200
    assert response.json()["id"] == service_id
    assert response.json()["name"] == "Fetch Me"


@pytest.mark.asyncio
async def test_get_service_not_found_returns_404(client: AsyncClient) -> None:
    response = await client.get("/api/v1/services/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_get_service_invalid_uuid_returns_422(client: AsyncClient) -> None:
    response = await client.get("/api/v1/services/not-a-uuid")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


# --- update service ---


@pytest.mark.asyncio
async def test_update_service_name(client: AsyncClient) -> None:
    created = await client.post(
        "/api/v1/services",
        json={"name": "Old Name"},
    )
    service_id = created.json()["id"]

    response = await client.patch(
        f"/api/v1/services/{service_id}",
        json={"name": "New Name"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


@pytest.mark.asyncio
async def test_update_service_preserves_omitted_fields(client: AsyncClient) -> None:
    created = await client.post(
        "/api/v1/services",
        json={"name": "Keep Description", "description": "Original"},
    )
    service_id = created.json()["id"]

    response = await client.patch(
        f"/api/v1/services/{service_id}",
        json={"name": "Updated Name"},
    )
    assert response.status_code == 200
    assert response.json()["description"] == "Original"


@pytest.mark.asyncio
async def test_update_service_not_found_returns_404(client: AsyncClient) -> None:
    response = await client.patch(
        "/api/v1/services/00000000-0000-0000-0000-000000000000",
        json={"name": "Ghost"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_update_service_conflict_returns_409(client: AsyncClient) -> None:
    await client.post("/api/v1/services", json={"name": "First"})
    second = await client.post("/api/v1/services", json={"name": "Second"})
    service_id = second.json()["id"]

    response = await client.patch(
        f"/api/v1/services/{service_id}",
        json={"name": "First"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


# --- delete service ---


@pytest.mark.asyncio
async def test_delete_service_success(client: AsyncClient) -> None:
    created = await client.post(
        "/api/v1/services",
        json={"name": "Delete Me"},
    )
    service_id = created.json()["id"]

    response = await client.delete(f"/api/v1/services/{service_id}")
    assert response.status_code == 204

    fetch = await client.get(f"/api/v1/services/{service_id}")
    assert fetch.status_code == 404


@pytest.mark.asyncio
async def test_delete_service_not_found_returns_404(client: AsyncClient) -> None:
    response = await client.delete(
        "/api/v1/services/00000000-0000-0000-0000-000000000000"
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_delete_service_with_active_incident_returns_409(
    client: AsyncClient,
) -> None:
    created = await client.post(
        "/api/v1/services",
        json={"name": "Busy Service"},
    )
    service_id = created.json()["id"]

    await client.post(
        "/api/v1/incidents",
        json={
            "title": "Blocking Incident",
            "severity": "low",
            "service_ids": [service_id],
        },
    )

    response = await client.delete(f"/api/v1/services/{service_id}")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


# --- request ID header ---


@pytest.mark.asyncio
async def test_response_includes_request_id_header(client: AsyncClient) -> None:
    response = await client.get("/api/v1/services")
    assert "x-request-id" in response.headers


@pytest.mark.asyncio
async def test_custom_request_id_is_echoed(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/services",
        headers={"x-request-id": "my-custom-id"},
    )
    assert response.headers["x-request-id"] == "my-custom-id"
