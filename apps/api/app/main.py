from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .open_meteo import OpenMeteoClient, OpenMeteoError
from .schemas import Report, ReportCreate, ResourceAssessment, RiskEvaluateRequest, RiskEvent, RiskRule, Watchpoint, WatchpointCreate, WeatherForecastResponse
from .store import REPORTS, RISK_EVENTS, RISK_RULES, WATCHPOINTS, add_watchpoint, now_utc

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
router = APIRouter(prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "meteo-resource-api"}


@router.get("/watchpoints", response_model=list[Watchpoint])
async def list_watchpoints() -> list[Watchpoint]:
    return list(WATCHPOINTS.values())


@router.post("/watchpoints", response_model=Watchpoint, status_code=201)
async def create_watchpoint(payload: WatchpointCreate) -> Watchpoint:
    return add_watchpoint(payload.name, payload.latitude, payload.longitude, payload.tags)


def _demo_forecast(watchpoint: Watchpoint) -> WeatherForecastResponse:
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    points = []
    for i in range(72):
        hour = now + timedelta(hours=i)
        points.append({
            "time": hour,
            "quality_flag": "estimated",
            "temperature_c": round(16 + 7 * ((i % 24) / 23), 1),
            "wind_speed_ms": round(4 + (i % 9) * 0.6, 1),
            "precipitation_mm": round(0.2 * (i % 5), 1),
            "cloud_cover_pct": 35 + (i * 7) % 55,
            "shortwave_radiation_wm2": max(0, round(620 * ((i % 24 - 6) / 8))) if 6 <= i % 24 <= 18 else 0,
        })
    from .schemas import WeatherPoint
    return WeatherForecastResponse(
        watchpoint=watchpoint,
        model="demo",
        fetched_at=now,
        source="demo",
        points=[WeatherPoint(**point) for point in points],
    )


@router.get("/weather/forecast", response_model=WeatherForecastResponse)
async def forecast(watchpoint_id: str = Query(...)) -> WeatherForecastResponse:
    watchpoint = WATCHPOINTS.get(watchpoint_id)
    if watchpoint is None:
        raise HTTPException(status_code=404, detail="关注点不存在")
    try:
        return await OpenMeteoClient(settings).forecast(watchpoint)
    except OpenMeteoError as exc:
        if settings.allow_demo_data:
            return _demo_forecast(watchpoint)
        raise HTTPException(status_code=502, detail=f"Open-Meteo 请求失败：{exc}") from exc


@router.get("/resources/assessment", response_model=ResourceAssessment)
async def resource_assessment(watchpoint_id: str = Query(...)) -> ResourceAssessment:
    forecast_data = await forecast(watchpoint_id)
    points = forecast_data.points
    mean_ghi = sum(point.shortwave_radiation_wm2 or 0 for point in points) / len(points)
    mean_wind = sum(point.wind_speed_ms or 0 for point in points) / len(points)
    return ResourceAssessment(
        watchpoint_id=watchpoint_id,
        solar_score=round(min(mean_ghi / 6, 100), 1),
        wind_score=round(min(mean_wind * 6, 100), 1),
        mean_ghi_wm2=round(mean_ghi, 1),
        mean_wind_speed_ms=round(mean_wind, 1),
        period_start=points[0].time,
        period_end=points[-1].time,
    )


@router.get("/risks/rules", response_model=list[RiskRule])
async def list_risk_rules() -> list[RiskRule]:
    return list(RISK_RULES.values())


@router.get("/risks/events")
async def list_risk_events() -> list[dict[str, Any]]:
    return [event.model_dump(mode="json") for event in RISK_EVENTS]


@router.post("/risks/evaluate", response_model=list[RiskEvent])
async def evaluate_risks(payload: RiskEvaluateRequest) -> list[RiskEvent]:
    if payload.watchpoint_id not in WATCHPOINTS:
        raise HTTPException(status_code=404, detail="关注点不存在")
    forecast_data = await forecast(payload.watchpoint_id)
    created: list[RiskEvent] = []
    for rule in RISK_RULES.values():
        if not rule.enabled:
            continue
        for point in forecast_data.points:
            value = getattr(point, rule.variable, None)
            if value is None:
                continue
            matched = {">": value > rule.threshold, ">=": value >= rule.threshold, "<": value < rule.threshold, "<=": value <= rule.threshold}[rule.operator]
            if matched:
                event = RiskEvent(
                    id=f"event-{rule.id}-{payload.watchpoint_id}-{point.time.strftime('%Y%m%d%H%M')}",
                    rule_id=rule.id,
                    rule_name=rule.name,
                    watchpoint_id=payload.watchpoint_id,
                    triggered_at=point.time,
                    evidence={"variable": rule.variable, "operator": rule.operator, "threshold": rule.threshold, "value": value, "quality_flag": point.quality_flag},
                )
                if not any(existing.id == event.id for existing in RISK_EVENTS):
                    RISK_EVENTS.append(event)
                    created.append(event)
                break
    return created


@router.get("/quality/summary")
async def quality_summary() -> dict[str, Any]:
    return {
        "sources": [
            {"name": name, "status": "unverified", "freshness_minutes": None, "coverage_percent": None}
            for name in ["Forecast", "Historical", "Ensemble", "Air Quality", "Marine", "Flood"]
        ],
        "updated_at": now_utc(),
    }


@router.get("/models")
async def model_summary() -> dict[str, Any]:
    return {"models": [{"name": name, "status": "available", "run_time": now_utc()} for name in ["ECMWF", "GFS", "ICON"]]}


@router.get("/reports", response_model=list[Report])
async def list_reports() -> list[Report]:
    return REPORTS


@router.post("/reports", response_model=Report, status_code=201)
async def create_report(payload: ReportCreate) -> Report:
    if payload.watchpoint_id not in WATCHPOINTS:
        raise HTTPException(status_code=404, detail="关注点不存在")
    forecast_data = await forecast(payload.watchpoint_id)
    mean_temp = round(sum(point.temperature_c or 0 for point in forecast_data.points) / len(forecast_data.points), 1)
    report = Report(
        id=f"report-{len(REPORTS) + 1}",
        report_type=payload.report_type,
        watchpoint_id=payload.watchpoint_id,
        title={"weather_brief": "气象简报", "resource_assessment": "资源评估报告", "risk_review": "风险复盘"}[payload.report_type],
        generated_at=now_utc(),
        source=forecast_data.source,
        summary={"model": forecast_data.model, "mean_temperature_c": mean_temp, "point_count": len(forecast_data.points), "quality_flags": sorted({point.quality_flag for point in forecast_data.points})},
    )
    REPORTS.append(report)
    return report


app.include_router(router)
