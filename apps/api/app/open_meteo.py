from datetime import datetime, timezone
from typing import Any

import httpx

from .config import Settings
from .schemas import WeatherForecastResponse, WeatherPoint, Watchpoint


class OpenMeteoError(RuntimeError):
    """Open-Meteo 服务不可用或响应格式不正确。"""


class OpenMeteoClient:
    def __init__(self, settings: Settings, transport: httpx.AsyncBaseTransport | None = None):
        self.settings = settings
        self.transport = transport

    async def forecast(self, watchpoint: Watchpoint) -> WeatherForecastResponse:
        params = {
            "latitude": watchpoint.latitude,
            "longitude": watchpoint.longitude,
            "hourly": "temperature_2m,wind_speed_10m,precipitation,cloud_cover,shortwave_radiation",
            "forecast_days": 3,
            "timezone": "UTC",
        }
        url = f"{self.settings.open_meteo_base_url.rstrip('/')}/forecast"
        try:
            async with httpx.AsyncClient(timeout=self.settings.open_meteo_timeout_seconds, transport=self.transport) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise OpenMeteoError(str(exc)) from exc
        return self._parse_forecast(watchpoint, payload, url)

    @staticmethod
    def _parse_forecast(watchpoint: Watchpoint, payload: dict[str, Any], source: str) -> WeatherForecastResponse:
        hourly = payload.get("hourly") or {}
        times = hourly.get("time") or []
        arrays = {
            "temperature_c": hourly.get("temperature_2m") or [],
            "wind_speed_ms": hourly.get("wind_speed_10m") or [],
            "precipitation_mm": hourly.get("precipitation") or [],
            "cloud_cover_pct": hourly.get("cloud_cover") or [],
            "shortwave_radiation_wm2": hourly.get("shortwave_radiation") or [],
        }
        units = payload.get("hourly_units") or {}
        wind_unit = units.get("wind_speed_10m")
        if wind_unit in {"km/h", "kmh"}:
            arrays["wind_speed_ms"] = [value / 3.6 if value is not None else None for value in arrays["wind_speed_ms"]]
        elif wind_unit in {"mph"}:
            arrays["wind_speed_ms"] = [value * 0.44704 if value is not None else None for value in arrays["wind_speed_ms"]]
        points: list[WeatherPoint] = []
        for index, timestamp in enumerate(times):
            values = {key: values[index] if index < len(values) else None for key, values in arrays.items()}
            points.append(WeatherPoint(time=datetime.fromisoformat(timestamp).replace(tzinfo=timezone.utc), **values))
        if not points:
            raise OpenMeteoError("Open-Meteo 响应缺少 hourly.time")
        return WeatherForecastResponse(
            watchpoint=watchpoint,
            model=str(payload.get("model") or payload.get("generationtime_ms", "open-meteo")),
            run_time=datetime.now(timezone.utc),
            source=source,
            points=points,
        )
