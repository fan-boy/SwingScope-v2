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

    # SMTP (works with Gmail, Resend, SendGrid)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

    # Alerts
    alert_email_enabled: bool = True
    alert_email_to: str = ""

    # Scheduler
    scheduler_enabled: bool = False   # opt-in
    scan_cron_schedule: str = "30 23 * * 1-5"   # 11:30 PM UTC Mon-Fri


settings = Settings()
