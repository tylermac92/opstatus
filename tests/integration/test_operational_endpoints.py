import pytest
from httpx import AsyncClient

# --- liveness probe ---


@pytest.mark.asyncio
async def test_liveness_returns_200(client: AsyncClient) -> None:
    response = await client.get("/health/live")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_liveness_returns_correct_body(client: AsyncClient) -> None:
    response = await client.get("/health/live")
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_liveness_response_is_fast(client: AsyncClient) -> None:
    import time

    start = time.perf_counter()
    await client.get("/health/live")
    duration_ms = (time.perf_counter() - start) * 1000
    assert duration_ms < 50


# --- readiness probe ---


@pytest.mark.asyncio
async def test_readiness_returns_200_when_db_available(
    client: AsyncClient,
) -> None:
    response = await client.get("/health/ready")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_readiness_returns_correct_body_when_healthy(
    client: AsyncClient,
) -> None:
    response = await client.get("/health/ready")
    body = response.json()
    assert body["status"] == "ok"
    assert body["checks"]["database"]["status"] == "ok"
    assert "duration_ms" in body["checks"]["database"]


@pytest.mark.asyncio
async def test_readiness_duration_ms_is_numeric(client: AsyncClient) -> None:
    response = await client.get("/health/ready")
    duration_ms = response.json()["checks"]["database"]["duration_ms"]
    assert isinstance(duration_ms, float | int)


@pytest.mark.asyncio
async def test_readiness_returns_503_when_db_unavailable(
    broken_db_client: AsyncClient,
) -> None:
    response = await broken_db_client.get("/health/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "unavailable"
    assert body["checks"]["database"]["status"] == "error"
    assert "duration_ms" in body["checks"]["database"]


# --- metrics endpoint ---


@pytest.mark.asyncio
async def test_metrics_returns_200(client: AsyncClient) -> None:
    response = await client.get("/metrics")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_metrics_content_type_is_plain_text(client: AsyncClient) -> None:
    response = await client.get("/metrics")
    assert "text/plain" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_metrics_contains_http_requests_total(client: AsyncClient) -> None:
    await client.get("/api/v1/services")
    response = await client.get("/metrics")
    assert "http_requests_total" in response.text


@pytest.mark.asyncio
async def test_metrics_contains_http_request_duration_seconds(
    client: AsyncClient,
) -> None:
    response = await client.get("/metrics")
    assert "http_request_duration_seconds" in response.text


@pytest.mark.asyncio
async def test_metrics_contains_active_incidents_total(
    client: AsyncClient,
) -> None:
    response = await client.get("/metrics")
    assert "active_incidents_total" in response.text


@pytest.mark.asyncio
async def test_metrics_contains_services_total(client: AsyncClient) -> None:
    response = await client.get("/metrics")
    assert "services_total" in response.text


@pytest.mark.asyncio
async def test_metrics_http_requests_total_increments(
    client: AsyncClient,
) -> None:
    # Make several API calls then confirm the counter is non-zero
    await client.get("/api/v1/services")
    await client.get("/api/v1/incidents")

    response = await client.get("/metrics")
    lines = response.text.splitlines()

    # Find the http_requests_total lines that have actual sample values
    counter_lines = [
        line
        for line in lines
        if line.startswith("http_requests_total{") and not line.startswith("#")
    ]
    assert len(counter_lines) > 0

    # At least one counter value should be non-zero
    values = [float(line.split()[-1]) for line in counter_lines]
    assert any(v > 0 for v in values)


@pytest.mark.asyncio
async def test_metrics_excludes_health_paths(client: AsyncClient) -> None:
    await client.get("/health/live")
    await client.get("/health/ready")

    response = await client.get("/metrics")
    assert "/health/live" not in response.text
    assert "/health/ready" not in response.text


@pytest.mark.asyncio
async def test_metrics_excludes_metrics_path_itself(
    client: AsyncClient,
) -> None:
    await client.get("/metrics")
    await client.get("/metrics")

    response = await client.get("/metrics")
    # The /metrics path should not appear as a label value in http_requests_total
    counter_lines = [
        line
        for line in response.text.splitlines()
        if line.startswith("http_requests_total{")
    ]
    assert not any('path="/metrics"' in line for line in counter_lines)
