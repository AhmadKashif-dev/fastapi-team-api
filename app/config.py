from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "team_db"
    POSTGRES_PORT: int = 5434
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5434/team_db"

    JWT_SECRET: str = "change-me-in-production-use-32-chars-min"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    MAIL_FROM: str = "noreply@team-api.local"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
