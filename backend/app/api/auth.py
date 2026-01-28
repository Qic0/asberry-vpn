# app/api/auth.py
from fastapi import APIRouter, Header, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.services.telegram import verify_init_data

router = APIRouter()


@router.get("/me")
def me(
    x_telegram_init_data: str = Header(...),
    db: Session = Depends(get_db),
):
    try:
        data = verify_init_data(x_telegram_init_data)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Telegram data")

    telegram_id = int(data["user[id]"])
    username = data.get("user[username]")

    user = (
        db.query(User)
        .filter(User.telegram_id == telegram_id)
        .first()
    )

    if not user:
        user = User(
            telegram_id=telegram_id,
            username=username,
            balance=10,  # 🎁 пробный период
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return {
        "id": user.id,
        "telegram_id": user.telegram_id,
        "username": user.username,
        "balance": user.balance,
        "created_at": user.created_at,
    }

