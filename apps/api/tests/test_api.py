from fastapi.testclient import TestClient

from app.main import app


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
    assert payload["points"][0]["quality_flag"] == "raw"


def test_resource_assessment() -> None:
    response = client.get("/api/v1/resources/assessment?watchpoint_id=wp-east")
    assert response.status_code == 200
    assert 0 <= response.json()["solar_score"] <= 100
