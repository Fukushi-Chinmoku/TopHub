from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Codely API"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = False

    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_db: str = "codely"
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    redis_host: str = "redis"
    redis_port: int = 6379

    session_idle_minutes: int = 30
    session_max_days: int = 7
    session_cookie_name: str = "session_id"
    session_cookie_secure: bool = False
    session_cookie_samesite: str = "lax"

    login_regex: str = r"^[a-zA-Z][a-zA-Z0-9_]{2,31}$"
    password_regex: str = r"^(?=.*[A-Za-z])(?=.*\d).{8,128}$"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"


settings = Settings()
