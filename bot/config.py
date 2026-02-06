from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    TG_BOT_TOKEN: str
    MINI_APP_URL: str

    class Config:
        env_file = "../.env"   # ВАЖНО: путь от папки bot
        extra = "ignore"

settings = Settings()
