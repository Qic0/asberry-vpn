from fastapi import (
    FastAPI,
    HTTPException,
    Request,
    Depends,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import User, VpnClient
from app.services.vpn_service import XUIClient
from app.auth import verify_telegram_init_data


app = FastAPI(title="Asburium VPN Mini App")

# ---------- STATIC ----------
app.mount(
    "/static",
    StaticFiles(directory="Mini_app_test/static"),
    name="static",
)

app.mount(
    "/frontend",
    StaticFiles(directory="Mini_app_test/frontend"),
    name="frontend",
)

# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- SCHEMAS ----------
class TelegramAuthPayload(BaseModel):
    initData: str


# ---------- DEPENDENCY ----------
async def get_current_user(request: Request) -> User:
    init_data = request.headers.get("X-Telegram-Init-Data")
    if not init_data:
        raise HTTPException(status_code=401, detail="No init data")

    data = verify_telegram_init_data(init_data)
    user_info = data.get("user")
    telegram_id = str(user_info["id"])

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            user = User(telegram_id=telegram_id)
            session.add(user)
            await session.commit()
            await session.refresh(user)

        return user


# ---------- MINI APP UI ----------
@app.get("/", response_class=HTMLResponse)
async def index():
    with open("Mini_app_test/frontend/index.html", encoding="utf-8") as f:
        return f.read()


# ---------- AUTH (MINI APP INIT) ----------
@app.post("/auth")
async def auth(payload: TelegramAuthPayload):
    try:
        data = verify_telegram_init_data(payload.initData)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid init data")

    telegram_id = str(data["user"]["id"])

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            user = User(telegram_id=telegram_id)
            session.add(user)
            await session.commit()
            await session.refresh(user)

        return JSONResponse({
            "telegram_id": user.telegram_id,
            "balance": user.balance,
        })


# ---------- VPN LIST ----------
@app.get("/vpn/list")
async def list_vpn(user: User = Depends(get_current_user)):
    return {
        "items": [
            {
                "id": v.id,
                "email": v.email,
                "vless_url": v.vless_url,
                "enabled": v.enabled,
            }
            for v in user.vpn_clients
        ]
    }


# ---------- VPN CREATE ----------
@app.post("/vpn/create")
async def create_vpn(user: User = Depends(get_current_user)):
    async with AsyncSessionLocal() as session:
        async with session.begin():

            # 🔢 формируем уникальное имя
            base_email = f"tg_{user.telegram_id}"

            result = await session.execute(
                select(VpnClient.email)
                .where(VpnClient.user_id == user.id)
            )
            existing = {row[0] for row in result.all()}

            email = base_email
            i = 1
            while email in existing:
                email = f"{base_email}/{i}"
                i += 1

            xui = XUIClient()
            try:
                client_id, vless_url = await xui.create_client(email=email)
            finally:
                await xui.close()

            vpn = VpnClient(
                user_id=user.id,
                xui_client_id=client_id,
                email=email,
                vless_url=vless_url,
                enabled=True,
            )

            session.add(vpn)

        return {
            "created": True,
            "email": email,
            "vless_url": vless_url,
        }


# ---------- VPN TOGGLE ----------
@app.post("/vpn/{vpn_id}/toggle")
async def toggle_vpn(vpn_id: int, user: User = Depends(get_current_user)):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            result = await session.execute(
                select(VpnClient)
                .where(VpnClient.id == vpn_id)
                .where(VpnClient.user_id == user.id)
            )
            vpn = result.scalar_one_or_none()

            if not vpn:
                raise HTTPException(status_code=404)

            xui = XUIClient()
            try:
                if vpn.enabled:
                    await xui.disable_client(vpn.xui_client_id)
                else:
                    await xui.enable_client(vpn.xui_client_id)
            finally:
                await xui.close()

            vpn.enabled = not vpn.enabled

        return {"enabled": vpn.enabled}


# ---------- VPN DELETE -----

