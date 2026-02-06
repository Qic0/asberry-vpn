from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.services.telegram_auth import verify_init_data

router = APIRouter()


@router.get("/api/me")
def me(request: Request, db: Session = Depends(get_db)):
    init_data = request.headers.get("X-Telegram-Init-Data")

    if not init_data:
        raise HTTPException(status_code=401, detail="No initData header")

    try:
        tg_user = verify_init_data(init_data)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

    telegram_id = int(tg_user["id"])
    first_name = tg_user.get("first_name")
    username = tg_user.get("username")

    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        user = User(
            telegram_id=telegram_id,
            first_name=first_name,
            username=username,
            balance_rub=10,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # обновляем данные профиля из Telegram (на случай изменений)
        changed = False
        if first_name and user.first_name != first_name:
            user.first_name = first_name
            changed = True
        if username and user.username != username:
            user.username = username
            changed = True
        if changed:
            db.commit()

    return {
        "telegram_id": user.telegram_id,
        "first_name": user.first_name,
        "username": user.username,
        "balance_rub": user.balance_rub,
    }
