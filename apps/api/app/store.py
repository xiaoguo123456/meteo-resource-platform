from datetime import datetime, timezone
from uuid import uuid4

from .schemas import RiskEvent, RiskRule, Watchpoint


def _watchpoint(id_: str, name: str, lat: float, lon: float, tags: list[str]) -> Watchpoint:
    return Watchpoint(id=id_, name=name, latitude=lat, longitude=lon, timezone="Asia/Shanghai", tags=tags)


WATCHPOINTS: dict[str, Watchpoint] = {
    "wp-east": _watchpoint("wp-east", "华东区域", 31.23, 121.47, ["重点区域"]),
    "wp-north": _watchpoint("wp-north", "华北区域", 39.90, 116.40, ["关注点"]),
}

RISK_RULES: dict[str, RiskRule] = {
    "rule-wind": RiskRule(id="rule-wind", name="大风提醒", variable="wind_speed_ms", operator=">=", threshold=12),
    "rule-rain": RiskRule(id="rule-rain", name="强降水提醒", variable="precipitation_mm", operator=">=", threshold=30),
}

RISK_EVENTS: list[RiskEvent] = []


def add_watchpoint(name: str, latitude: float, longitude: float, tags: list[str]) -> Watchpoint:
    id_ = f"wp-{uuid4().hex[:10]}"
    item = _watchpoint(id_, name, latitude, longitude, tags)
    WATCHPOINTS[id_] = item
    return item


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
