from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = (
        "postgresql+asyncpg://book_catalog:book_catalog@localhost:5432/book_catalog"
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
