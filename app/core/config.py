from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    app_name: str = "Substrate"
    app_env: str = "development"
    debug: bool = True

    # PostgreSQL
    database_url: str

    # Redis
    redis_url: str

    # OpenAI
    openai_api_key: str
    embedding_model: str = "text-embedding-3-small"
    chat_model: str = "gpt-4o"

    # Supabase
    supabase_url: str
    supabase_jwt_secret: str

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )


settings = Settings()