from functools import cached_property
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/ (este fichero está en backend/app/shared/infrastructure/config.py)
BACKEND_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/oncologico"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    CORS_ORIGINS: str = "http://localhost:4321,http://localhost:5173"
    STORAGE_DIR: Path = Path("storage")
    MAX_UPLOAD_MB: int = 25

    @field_validator("STORAGE_DIR")
    @classmethod
    def _absolute_storage_dir(cls, value: Path) -> Path:
        """Ruta relativa → relativa a backend/, no al directorio desde el que se arranca uvicorn."""
        return value if value.is_absolute() else (BACKEND_ROOT / value).resolve()

    @property
    def database_url_async(self) -> str:
        url = self.DATABASE_URL
        for prefix in ("postgresql://", "postgres://"):
            if url.startswith(prefix):
                return url.replace(prefix, "postgresql+asyncpg://", 1)
        return url

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @cached_property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024


settings = Settings()
