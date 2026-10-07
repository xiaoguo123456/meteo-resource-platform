from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class Watchpoint(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    timezone: str = "UTC"
    tags: list[str] = Field(default_factory=list)


class WatchpointCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    tags: list[str] = Field(default_factory=list)


class WeatherPoint(BaseModel):
    time: datetime
    temperature_c: float | None = None
    wind_speed_ms: float | None = None
    precipitation_mm: float | None = None
    cloud_cover_pct: float | None = None
    shortwave_radiation_wm2: float | None = None
    quality_flag: Literal["raw", "interpolated", "estimated", "missing", "corrected"] = "raw"


class WeatherForecastResponse(BaseModel):
    watchpoint: Watchpoint
    model: str
    run_time: datetime
    source: str
    points: list[WeatherPoint]


class ResourceAssessment(BaseModel):
    watchpoint_id: str
    solar_score: float
    wind_score: float
    mean_ghi_wm2: float
    mean_wind_speed_ms: float
    period_start: datetime
    period_end: datetime
    quality_flag: str = "estimated"


class RiskRule(BaseModel):
    id: str
    name: str
    variable: Literal["wind_speed_ms", "precipitation_mm", "temperature_c", "visibility_m"]
    operator: Literal[">", ">=", "<", "<="]
    threshold: float
    enabled: bool = True


class RiskEvent(BaseModel):
    id: str
    rule_id: str
    rule_name: str
    watchpoint_id: str
    status: Literal["open", "acknowledged", "closed"] = "open"
    triggered_at: datetime
    evidence: dict[str, Any]
