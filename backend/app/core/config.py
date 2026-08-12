from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "FinSight API"
    environment: str = "development"
    
    # Database
    postgres_user: str = "postgres"
    postgres_password: str = "password"
    postgres_db: str = "finsight_db"
    postgres_host: str = "localhost"
    postgres_port: str = "5432"
    
    # Optional Database URL directly
    database_url: str | None = None

    # External APIs
    alpha_vantage_api_key: str = ""
    fred_api_key: str = ""
    news_api_key: str = ""
    
    # SEC EDGAR
    sec_user_agent: str = "FinSight/1.0 (developer@example.com)"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def sync_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

settings = Settings()
