from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "sqlite:///./barrio_pizza.db"
    allowed_origins: str | None = None
    backend_cors_origins: str = "http://localhost:5173"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.6-flash"
    gemini_daily_limit: int = 1500

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        origins = self.allowed_origins or self.backend_cors_origins
        return [origin.strip() for origin in origins.split(",") if origin.strip()]


settings = Settings()
