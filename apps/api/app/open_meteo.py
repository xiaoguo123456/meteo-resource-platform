from datetime import datetime, timezone
from typing import Any

import httpx

from .config import Settings
from .schemas import WeatherForecastResponse, WeatherGridPoint, WeatherPoint, Watchpoint


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
            "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation,cloud_cover,shortwave_radiation",
            "forecast_days": 3,
            "timezone": "UTC",
            "wind_speed_unit": "ms",
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

    async def grid(self, coordinates: list[tuple[float, float]]) -> list[WeatherGridPoint]:
        """读取一组网格中心点的当前小时场，供地图矢量层使用。"""
        if not coordinates:
            return []
        params = {
            "latitude": ",".join(f"{latitude:.4f}" for latitude, _ in coordinates),
            "longitude": ",".join(f"{longitude:.4f}" for _, longitude in coordinates),
            "hourly": "temperature_2m,wind_speed_10m,wind_direction_10m,cloud_cover,precipitation,shortwave_radiation",
            "forecast_days": 1,
            "timezone": "UTC",
            "wind_speed_unit": "ms",
        }
        url = f"{self.settings.open_meteo_base_url.rstrip('/')}/forecast"
        try:
            async with httpx.AsyncClient(timeout=self.settings.open_meteo_timeout_seconds, transport=self.transport) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise OpenMeteoError(str(exc)) from exc

        locations = payload if isinstance(payload, list) else [payload]
        result: list[WeatherGridPoint] = []
        for index, location in enumerate(locations):
            if index >= len(coordinates) or not isinstance(location, dict):
                continue
            hourly = location.get("hourly") or {}
            times = hourly.get("time") or []
            if not times:
                continue
            at = 0
            units = location.get("hourly_units") or {}
            wind = (hourly.get("wind_speed_10m") or [None])[at]
            if units.get("wind_speed_10m") in {"km/h", "kmh"} and wind is not None:
                wind /= 3.6
            elif units.get("wind_speed_10m") == "mph" and wind is not None:
                wind *= 0.44704
            timestamp = datetime.fromisoformat(times[at])
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            def value(name: str) -> Any:
                values = hourly.get(name) or []
                return values[at] if at < len(values) else None
            latitude, longitude = coordinates[index]
            values = {
                "temperature_c": value("temperature_2m"),
                "wind_speed_ms": wind,
                "wind_direction_deg": value("wind_direction_10m"),
                "cloud_cover_pct": value("cloud_cover"),
                "precipitation_mm": value("precipitation"),
                "shortwave_radiation_wm2": value("shortwave_radiation"),
            }
            result.append(WeatherGridPoint(latitude=latitude, longitude=longitude, valid_time=timestamp.astimezone(timezone.utc), quality_flag="missing" if any(item is None for item in values.values()) else "raw", **values))
        if not result:
            raise OpenMeteoError("Open-Meteo 响应缺少网格 hourly 数据")
        return result

    @staticmethod
    def _parse_forecast(watchpoint: Watchpoint, payload: dict[str, Any], source: str) -> WeatherForecastResponse:
        hourly = payload.get("hourly") or {}
        times = hourly.get("time") or []
        arrays = {
            "temperature_c": hourly.get("temperature_2m") or [],
            "relative_humidity_pct": hourly.get("relative_humidity_2m") or [],
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
            parsed_time = datetime.fromisoformat(timestamp)
            if parsed_time.tzinfo is None:
                parsed_time = parsed_time.replace(tzinfo=timezone.utc)
            points.append(WeatherPoint(time=parsed_time.astimezone(timezone.utc),
                                       quality_flag="missing" if any(v is None for v in values.values()) else "raw", **values))
        if not points:
            raise OpenMeteoError("Open-Meteo 响应缺少 hourly.time")
        return WeatherForecastResponse(
            watchpoint=watchpoint,
            model=str(payload.get("model") or "best_match"),
            fetched_at=datetime.now(timezone.utc),
            source=source,
            points=points,
        )
