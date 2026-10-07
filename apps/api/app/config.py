from functools import lru_cache
import os

from pydantic import BaseModel, Field


class Settings(BaseModel):
    app_name: str = "气象资源空间智能平台"
    open_meteo_base_url: str = Field(default="http://localhost:8090/v1", alias="OPEN_METEO_BASE_URL")
    open_meteo_timeout_seconds: float = Field(default=12.0, alias="OPEN_METEO_TIMEOUT_SECONDS")
    allow_demo_data: bool = Field(default=True, alias="ALLOW_DEMO_DATA")
    cors_origins: str = Field(default="http://localhost:5173", alias="CORS_ORIGINS")

    model_config = {"populate_by_name": True}

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    values = {
        key: value
        for key, value in os.environ.items()
        if key in {"OPEN_METEO_BASE_URL", "OPEN_METEO_TIMEOUT_SECONDS", "ALLOW_DEMO_DATA", "CORS_ORIGINS"}
    }
    if values.get("ALLOW_DEMO_DATA") is not None:
        values["ALLOW_DEMO_DATA"] = values["ALLOW_DEMO_DATA"].lower() in {"1", "true", "yes"}
    return Settings(**values)
