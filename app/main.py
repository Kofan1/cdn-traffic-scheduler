"""A deterministic CDN endpoint selection service using synthetic endpoint data."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


class Endpoint(BaseModel):
    id: str
    provider: str
    region: str
    latency_ms: float = Field(gt=0)
    availability: float = Field(ge=0, le=1)
    load: float = Field(ge=0, le=1)
    cost_per_gb: float = Field(ge=0)
    healthy: bool = True


class ScheduleRequest(BaseModel):
    region: str
    size_gb: float = Field(default=1, gt=0, le=10_000)


class ScheduleResponse(BaseModel):
    endpoint_id: str
    provider: str
    region: str
    score: float
    estimated_cost: float
    reasons: list[str]
    alternatives: list[dict[str, Any]]
    selected_at: datetime


app = FastAPI(title="CDN Traffic Scheduler", version="1.0.0")

ENDPOINTS: dict[str, Endpoint] = {
    "edge-us-west": Endpoint(id="edge-us-west", provider="self-built", region="us-west", latency_ms=42, availability=.999, load=.35, cost_per_gb=.018),
    "edge-us-central": Endpoint(id="edge-us-central", provider="vendor-a", region="us-central", latency_ms=58, availability=.998, load=.25, cost_per_gb=.012),
    "edge-us-east": Endpoint(id="edge-us-east", provider="vendor-b", region="us-east", latency_ms=92, availability=.997, load=.20, cost_per_gb=.009),
    "edge-eu-west": Endpoint(id="edge-eu-west", provider="vendor-a", region="eu-west", latency_ms=110, availability=.999, load=.30, cost_per_gb=.015),
}


def endpoint_score(endpoint: Endpoint) -> float:
    """Lower is better; weights intentionally favor latency and reliability."""
    latency_component = min(endpoint.latency_ms / 200, 1) * 45
    load_component = endpoint.load * 15
    cost_component = min(endpoint.cost_per_gb / .03, 1) * 20
    reliability_component = (1 - endpoint.availability) * 20_000
    return round(latency_component + load_component + cost_component + reliability_component, 4)


def choose_endpoint(request: ScheduleRequest) -> ScheduleResponse:
    candidates = [
        endpoint for endpoint in ENDPOINTS.values()
        if endpoint.region == request.region and endpoint.healthy
    ]
    if not candidates:
        candidates = [endpoint for endpoint in ENDPOINTS.values() if endpoint.healthy]
    if not candidates:
        raise HTTPException(status_code=503, detail="No healthy CDN endpoints available")

    ranked = sorted(candidates, key=endpoint_score)
    selected = ranked[0]
    score = endpoint_score(selected)
    reasons = [f"latency={selected.latency_ms:.0f}ms", f"availability={selected.availability:.3f}"]
    if selected.load < .5:
        reasons.append("moderate_load")
    if selected.cost_per_gb == min(item.cost_per_gb for item in ranked):
        reasons.append("lowest_cost_candidate")
    alternatives = [
        {"endpoint_id": item.id, "score": endpoint_score(item), "estimated_cost": round(item.cost_per_gb * request.size_gb, 4)}
        for item in ranked[1:]
    ]
    return ScheduleResponse(
        endpoint_id=selected.id,
        provider=selected.provider,
        region=selected.region,
        score=score,
        estimated_cost=round(selected.cost_per_gb * request.size_gb, 4),
        reasons=reasons,
        alternatives=alternatives,
        selected_at=datetime.now(timezone.utc),
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/endpoints", response_model=list[Endpoint])
def list_endpoints() -> list[Endpoint]:
    return list(ENDPOINTS.values())


@app.patch("/v1/endpoints/{endpoint_id}/health", response_model=Endpoint)
def update_health(endpoint_id: str, healthy: bool) -> Endpoint:
    endpoint = ENDPOINTS.get(endpoint_id)
    if endpoint is None:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    endpoint.healthy = healthy
    return endpoint


@app.post("/v1/schedule", response_model=ScheduleResponse)
def schedule(request: ScheduleRequest) -> ScheduleResponse:
    return choose_endpoint(request)

