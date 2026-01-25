from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from datetime import datetime

from app.database import AsyncSessionLocal
from app.models import User
from app.config import settings
from Mini_app_test.backend.auth import verify_telegram_init_data

router = APIRouter(prefix="/api")


# ---------- AUTH DEP ----------
async def get_current_user(x_telegram_init_data: str = Header(...)):
    tg_data = verify_telegram_init_data(x_telegram_init_data)
    telegram_id = str(tg_data["user"]["id"])

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return user


# ---------- /me ----------
@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    return {
        "telegram_id": user.telegram_id,
        "username": f"Asburium",
        "balance": user.balance,
        "subscription_active": user.subscription_active,
        "vpn_status": "active" if user.subscription_active else "disabled",
        "vpn_price_per_day": 5,
    }


# ---------- /vpn ----------
@router.get("/vpn")
async def vpn(user: User = Depends(get_current_user)):
    return {
        "client_name": f"Asberry-vpn-tg_{user.telegram_id}",
        "telegram_id": user.telegram_id,
        "status": "active" if user.subscription_active else "disabled",
        "price_per_day": 5,
        "vless_url": user.subscription_url,
        "devices": [
            {
                "name": "iPhone 17 Pro Max",
                "ip": "—"
            }
        ],
    }


# ---------- /referrals ----------
@router.get("/referrals")
async def referrals(user: User = Depends(get_current_user)):
    async with AsyncSessionLocal() as session:
        rows = await session.execute(
            """
            SELECT referred_user_id, amount, created_at
            FROM referral_transactions
            WHERE referrer_id = :rid
            ORDER BY created_at DESC
            """,
            {"rid": user.telegram_id},
        )

        transactions = [
            {
                "user": row[0],
                "amount": row[1],
                "date": row[2].strftime("%Y-%m-%d"),
            }
            for row in rows
        ]

    return {
        "referral_link": f"https://t.me/AsburiumBot?start=ref_{user.telegram_id}",
        "total_earned": sum(t["amount"] for t in transactions),
        "transactions": transactions,
    }


# ---------- /topup ----------
@router.get("/topup")
async def topup():
    return {
        "url": "https://t.me/AsburiumBot"
    }

