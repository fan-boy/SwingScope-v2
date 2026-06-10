from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str

    # Supabase
    supabase_url: str = ""
    supabase_service_role_key: str = ""

    # Alpaca
    alpaca_api_key: str = ""
    alpaca_api_secret: str = ""
    alpaca_base_url: str = "https://paper-api.alpaca.markets"

    # Finnhub
    finnhub_api_key: str = ""

    # App
    secret_key: str = "changeme"
    environment: str = "development"
    mock_mode: bool = False


settings = Settings()
