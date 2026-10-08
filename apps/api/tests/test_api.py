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


def test_forecast_accepts_map_coordinates() -> None:
    response = client.get("/api/v1/weather/forecast?latitude=22.5431&longitude=114.0579")
    assert response.status_code == 200
    assert response.json()["watchpoint"]["name"] == "地图选点"
    assert response.json()["watchpoint"]["latitude"] == 22.5431


def test_weather_grid_returns_current_vectors() -> None:
    response = client.get("/api/v1/weather/grid?min_latitude=20&max_latitude=30&min_longitude=110&max_longitude=120&step=10")
    assert response.status_code == 200
    assert response.json()[0]["wind_direction_deg"] == 90


def test_resource_assessment() -> None:
    response = client.get("/api/v1/resources/assessment?watchpoint_id=wp-east")
    assert response.status_code == 200
    assert 0 <= response.json()["solar_score"] <= 100


def test_risk_evaluation_and_report_creation() -> None:
    risk = client.post("/api/v1/risks/evaluate", json={"watchpoint_id": "wp-east"})
    assert risk.status_code == 200
    assert isinstance(risk.json(), list)
    report = client.post("/api/v1/reports", json={"report_type": "weather_brief", "watchpoint_id": "wp-east"})
    assert report.status_code == 201
    assert report.json()["source"] == "demo"


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


def test_open_meteo_grid_parses_multi_location_payload() -> None:
    payload = [
        {
            "hourly_units": {"wind_speed_10m": "km/h"},
            "hourly": {
                "time": ["2026-10-07T00:00"],
                "temperature_2m": [20],
                "wind_speed_10m": [36],
                "wind_direction_10m": [90],
                "cloud_cover": [50],
                "precipitation": [0],
                "shortwave_radiation": [100],
            },
        },
    ]

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    transport = httpx.MockTransport(handler)
    client = OpenMeteoClient(Settings(OPEN_METEO_BASE_URL="http://test/v1"), transport=transport)
    import asyncio
    result = asyncio.run(client.grid([(30, 120)]))
    assert result[0].wind_speed_ms == 10
    assert result[0].wind_direction_deg == 90
