import httpx
import os

from fastapi.testclient import TestClient

os.environ["ALLOW_DEMO_DATA"] = "true"

from app.main import app
from app.config import Settings
from app.open_meteo import OpenMeteoClient
from app.schemas import Watchpoint


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_and_list_watchpoint() -> None:
    response = client.post("/api/v1/watchpoints", json={"name": "测试区域", "latitude": 30, "longitude": 120})
    assert response.status_code == 201
    watchpoint_id = response.json()["id"]
    listed = client.get("/api/v1/watchpoints")
    assert listed.status_code == 200
    assert any(item["id"] == watchpoint_id for item in listed.json())


def test_demo_forecast_has_quality_and_points() -> None:
    response = client.get("/api/v1/weather/forecast?watchpoint_id=wp-east")
    assert response.status_code == 200
    payload = response.json()
    assert payload["points"]
    assert payload["points"][0]["quality_flag"] == "estimated"


def test_resource_assessment() -> None:
    response = client.get("/api/v1/resources/assessment?watchpoint_id=wp-east")
    assert response.status_code == 200
    assert 0 <= response.json()["solar_score"] <= 100


def test_open_meteo_converts_kmh_to_ms() -> None:
    payload = {
        "model": "ecmwf_ifs",
        "hourly_units": {"wind_speed_10m": "km/h"},
        "hourly": {
            "time": ["2026-10-07T00:00"],
            "temperature_2m": [20],
            "wind_speed_10m": [36],
            "precipitation": [0],
            "cloud_cover": [50],
            "shortwave_radiation": [100],
        },
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    transport = httpx.MockTransport(handler)
    client = OpenMeteoClient(Settings(OPEN_METEO_BASE_URL="http://test/v1"), transport=transport)
    import asyncio
    result = asyncio.run(client.forecast(Watchpoint(id="wp", name="测试", latitude=0, longitude=0)))
    assert result.points[0].wind_speed_ms == 10
    assert result.model == "ecmwf_ifs"
