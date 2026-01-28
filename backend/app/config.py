from pathlib import Path
from pydantic_settings import BaseSettings


BASE_DIR = Path(__file__).resolve().parents[2]  # /Asberry_vpn

class Settings(BaseSettings):
    TG_BOT_TOKEN: str
    DATABASE_URL: str

    class Config:
        env_file = BASE_DIR / ".env"
        extra = "ignore"


settings = Settings()

