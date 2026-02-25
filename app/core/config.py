from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    database_url: str
    log_level: str = "INFO"
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000


settings = Settings()  # type: ignore[call-arg]
