from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./signing.db"
    secret_key: str = "change-this-key"
    access_token_expire_minutes: int = 480
    smtp_host: str = "smtp-relay.brevo.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "alex@finanz-surfer.de"
    app_env: str = "development"

    model_config = {"env_file": ".env"}


settings = Settings()
