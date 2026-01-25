from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from Mini_app_test.backend.auth import verify_telegram_init_data
from app.database import AsyncSessionLocal
from app.models import User, VpnClient
from app.services.vpn_service import XUIClient


app = FastAPI(title="Asburium VPN Mini App")

# ================= STATIC =================
app.mount("/static", StaticFiles(directory="Mini_app_test/static"), name="static")
app.mount("/frontend", StaticFiles(directory="Mini_app_test/frontend"), name="frontend")

# ================= CORS =================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= DB =================
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

# ================= HELPERS =================
async def get_user_from_telegram(
    request: Request,
    session: AsyncSession,
) -> User:
    init_data = request.headers.get("X-Telegram-Init-Data")
    if not init_data:
        raise HTTPException(status_code=401, detail="No Telegram init data")

    data = verify_telegram_init_data(init_data)
    telegram_id = str(data["user"]["id"])

    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        # ❗ Mini App НИКОГДА не создаёт пользователя
        raise HTTPException(
            status_code=404,
            detail="User must be created via bot /start",
        )

    return user

# ================= UI =================
@app.get("/", response_class=HTMLResponse)
async def index():
    with open("Mini_app_test/frontend/index.html", encoding="utf-8") as f:
        return f.read()

# ================= API: ME =================
@app.get("/api/me")
async def api_me(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    user = await get_user_from_telegram(request, session)

    return {
        "telegram_id": user.telegram_id,
        "balance": user.balance,
        "subscription_active": user.subscription_active,
    }

# ================= API: VPN LIST =================
@app.get("/api/vpn/list")
async def api_vpn_list(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    user = await get_user_from_telegram(request, session)

    result = await session.execute(
        select(VpnClient).where(VpnClient.user_id == user.id)
    )
    clients = result.scalars().all()

    return [
        {
            "id": c.id,
            "email": c.email,
            "vless_url": c.vless_url,
            "enabled": c.enabled,
        }
        for c in clients
    ]

# ================= API: VPN CREATE =================
@app.post("/api/vpn/create")
async def api_vpn_create(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    user = await get_user_from_telegram(request, session)

    xui = XUIClient()
    try:
        email = f"tg_{user.telegram_id}"
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
    await session.commit()

    return {"status": "ok"}

# ================= HEALTH =================
@app.get("/health")
async def health():
    return {"status": "ok"}

