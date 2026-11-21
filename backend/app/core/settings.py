from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "KahveCell API"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./backend/kahvecell.db"
    frontend_origin: str = "http://localhost:5173"
    jwt_secret: str = "kahvecell-development-secret-change-in-production"
    qr_signing_secret: str = "kahvecell-development-qr-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60
    refresh_token_days: int = 30

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()