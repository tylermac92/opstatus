from prometheus_client import Counter, Gauge, Histogram

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP Requests",
    ["method", "path", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

active_incidents_total = Gauge(
    "active_incidents_total",
    "Count of non-resolved incidents",
    ["severity"],
)

services_total = Gauge(
    "services_total",
    "Total number of tracked services",
)
