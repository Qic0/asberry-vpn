from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TG_BOT_TOKEN: str
    MINI_APP_URL: str
    DATABASE_URL: str = "sqlite:///./app.db"

    class Config:
        env_file = ".env"


settings = Settings()

XUI_BASE_URL = "https://xui.dycani.ru:31308"
XUI_PANEL_PATH = "xsYuxKzG2acQjiEbID"

XUI_USERNAME = "bW4ctc2eNl"
XUI_PASSWORD = "hUVcAlcnTM"

XUI_INBOUND_ID = 2

