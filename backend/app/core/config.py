from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Peluqueri-APP API"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "postgresql://admin:adminpassword@db:5432/peluqueriapp"
    REDIS_URL: str = "redis://redis:6379/0"
    SECRET_KEY: str = "super_secret_jwt_key_peluqueriapp_2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120

    class Config:
        env_file = ".env"

settings = Settings()