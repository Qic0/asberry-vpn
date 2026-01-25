from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from Mini_app_test.backend.auth import verify_telegram_init_data
from app.database import AsyncSessionLocal
from app.models import User
from app.services.vpn_service import XUIClient

from sqlalchemy import select


app = FastAPI(title="VPN Mini App")

# ================= STATIC =================
app.mount(
    "/static",
    StaticFiles(directory="Mini_app_test/static"),
    name="static"
)

# ================= CORS =================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Telegram Mini App
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= MODELS =================
class TelegramAuthPayload(BaseModel):
    initData: str


# ================= MINI APP UI =================
@app.get("/", response_class=HTMLResponse)
async def index():
    """
    Mini App UI
    HTML намеренно остаётся тут (ты позже вынесешь в frontend)
    """
    with open("Mini_app_test/frontend/index.html", "r", encoding="utf-8") as f:
        return f.read()


# ================= AUTH =================
@app.post("/auth")
async def auth(payload: TelegramAuthPayload):
    """
    Авторизация Mini App через Telegram initData
    """
    try:
        data = verify_telegram_init_data(payload.initData)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid initData")

    user_info = data.get("user")
    if not user_info:
        raise HTTPException(status_code=401, detail="No user")

    telegram_id = str(user_info["id"])

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return JSONResponse({
            "telegram_id": telegram_id,
            "balance": user.balance,
            "subscription_active": user.subscription_active,
            "subscription_until": user.subscription_until.isoformat()
            if user.subscription_until else None,
            "subscription_url": user.subscription_url,
            "xui_client_id": user.xui_client_id,
        })


# ================= CREATE VPN =================
@app.post("/vpn/create")
async def create_vpn(payload: TelegramAuthPayload):
    """
    Создание нового VPN-подключения для пользователя (можно несколько)
    """

    # ---------- AUTH ----------
    try:
        data = verify_telegram_init_data(payload.initData)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Telegram initData")

    telegram_id = str(data["user"]["id"])

    async with AsyncSessionLocal() as session:
        async with session.begin():

            # ---------- USER ----------
            result = await session.execute(
                select(User)
                .where(User.telegram_id == telegram_id)
                .with_for_update()
            )
            user = result.scalar_one_or_none()

            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            # ---------- GENERATE UNIQUE EMAIL ----------
            base_email = f"tg_{telegram_id}"

            result = await session.execute(
                select(VpnClient.xui_email)
                .where(VpnClient.user_id == user.id)
            )
            existing_emails = {row[0] for row in result.all()}

            email = base_email
            counter = 1
            while email in existing_emails:
                email = f"{base_email}/{counter}"
                counter += 1

            # ---------- CREATE IN X-UI ----------
            xui = XUIClient()
            try:
                xui_client_id, vless_url = await xui.create_client(
                    email=email
                )
            finally:
                await xui.close()

            # ---------- SAVE VPN ----------
            vpn = VpnClient(
                user_id=user.id,
                xui_client_id=xui_client_id,
                xui_email=email,
                subscription_url=vless_url,
                active=False,
            )

            session.add(vpn)

        # commit here automatically

    return JSONResponse({
        "created": True,
        "vpn": {
            "id": vpn.id,
            "email": vpn.xui_email,
            "subscription_url": vpn.subscription_url,
            "active": vpn.active,
        }
    })

# ================= OPEN HAPP =================
@app.get("/open/happ")
async def open_happ():
    """
    Редирект в Happ / любой клиент по vless://
    """
    vless_url = (
        "vless://244c819b-b9cd-45e7-b908-69737073e7ed"
        "@147.45.152.14:8443"
        "?type=ws&encryption=none&path=%2Fupload%2Fsession"
        "&security=none"
        "#VPN"
    )
    return RedirectResponse(url=vless_url, status_code=302)


# ================= HEALTH =================
@app.get("/health")
async def health():
    return {"status": "ok"}

