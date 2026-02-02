from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TG_BOT_TOKEN: str
    MINI_APP_URL: str
    DATABASE_URL: str = "sqlite:///./app.db"

    class Config:
        env_file = ".env"


settings = Settings()

