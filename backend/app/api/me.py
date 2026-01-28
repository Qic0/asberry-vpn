# app/api/me.py

from fastapi import APIRouter, Header, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User
from app.api.deps import verify_telegram_init_data

router = APIRouter()


@router.get("/me")
def get_me(
    x_telegram_init_data: str = Header(..., alias="X-Telegram-Init-Data")
):
    try:
        data = verify_telegram_init_data(x_telegram_init_data)
        tg_user = data["user"]
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

    db: Session = SessionLocal()

    user = db.query(User).filter(
        User.telegram_id == tg_user["id"]
    ).first()

    if not user:
        user = User(
            telegram_id=tg_user["id"],
            balance=10
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return {
        "id": user.id,
        "telegram_id": user.telegram_id,
        "balance": user.balance
    }

