import os
from dotenv import load_dotenv
# from pydantic import BaseSettings
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    TEST_DATABASE_URL: str = os.getenv("TEST_DATABASE_URL")
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    STRIPE_API_KEY: str = os.getenv("STRIPE_API_KEY")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET")

    class Config:
        env_file = ".env"

settings = Settings()
