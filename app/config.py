from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "team_db"
    POSTGRES_PORT: int = 5434   
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5434/team_db"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
