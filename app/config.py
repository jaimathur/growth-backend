from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_user: str = "pennywise"
    db_password: str = ""
    db_name: str = "pennywise"
    db_pool_size: int = Field(10, ge=1, le=100)

    jwt_secret: str = Field(..., min_length=32, description="HMAC signing key, >= 32 chars")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(60, ge=1)

    cors_origins: str = "http://localhost:5173"
    allow_registration: bool = True

    @field_validator("jwt_algorithm")
    @classmethod
    def _hmac_only(cls, v: str) -> str:
        if v not in {"HS256", "HS384", "HS512"}:
            raise ValueError("JWT_ALGORITHM must be one of HS256, HS384, HS512")
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
