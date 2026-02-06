from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Telegram ---
    TG_BOT_TOKEN: str

    # --- App ---
    MINI_APP_URL: str | None = None
    DATABASE_URL: str = "sqlite:///./asburium.db"
    BILLING_ENABLED: bool = True
    BILLING_INTERVAL_SECONDS: int = 60 * 60 * 24  # 24h

    # --- VLESS remark ---
    VLESS_REMARK_PREFIX: str = "Asberry"
    VLESS_REMARK_FLAG: str | None = "🇳🇱"

    # --- X-UI ---
    XUI_BASE_URL: str
    # Some installations use a path prefix like "/<panel_id>" (3x-ui behind proxy).
    # If your panel lives at the root, keep it empty.
    XUI_PANEL_PATH: str = ""
    XUI_USERNAME: str
    XUI_PASSWORD: str
    XUI_INBOUND_ID: int
    XUI_HOST: str | None = None  # домен/айпи для ссылки (если отличается от BASE_URL)
    XUI_REALITY_PUBLIC_KEY: str | None = None  # pbk (если нужно форсировать)

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
