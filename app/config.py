from dotenv import load_dotenv
import os

load_dotenv()


class Settings:
    TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")

    DB_URL = os.getenv(
        "DB_URL",
        "sqlite+aiosqlite:///./vpn.db"
    )

    # X-UI
    XUI_PANEL_URL = "https://147.45.152.14:54321/4xd7kwBKlq4FNnfxKI"
    XUI_SUB_URL = "https://147.45.152.14:2096"


    XUI_HOST = "147.45.152.14"
    XUI_SERVER_HOST = "147.45.152.14"



    XUI_USERNAME = os.getenv("XUI_USERNAME")
    XUI_PASSWORD = os.getenv("XUI_PASSWORD")
    XUI_INBOUND_ID = os.getenv ("XUI_INBOUND_ID")

    XUI_REALITY_PUBLIC_KEY = os.getenv("XUI_REALITY_PUBLIC_KEY")

settings = Settings()

