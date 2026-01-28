#Dependency: получить текущего пользователя
# app/api/deps.py
from fastapi import Header, HTTPException
from app.config import settings
from urllib.parse import parse_qsl
import hashlib
import hmac
import json

from app.database import SessionLocal
from app.models.user import User


def verify_telegram_init_data(init_data: str) -> dict:
    """
    Verify Telegram WebApp initData signature and return parsed data.
    The returned dict will contain 'user' as a parsed dict (not a JSON string) when possible.
    Raises ValueError on invalid data/signature.
    """
    if not init_data:
        raise ValueError("Empty initData")

    # parse_qsl -> percent-decoded key/value pairs
    data = dict(parse_qsl(init_data, keep_blank_values=True))

    if "hash" not in data:
        raise ValueError("No hash in initData")

    received_hash = data.pop("hash")

    # create check string according to Telegram docs
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(data.items())
    )

    # secret key is sha256(bot_token)
    secret_key = hashlib.sha256(
        settings.TG_BOT_TOKEN.encode()
    ).digest()

    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise ValueError("Invalid initData signature")

    # parse user field to dict if it's a JSON string
    user_raw = data.get("user")
    if user_raw:
        try:
            data["user"] = json.loads(user_raw)
        except Exception:
            # keep original if parsing fails
            pass

    return data


def get_current_user(
    x_telegram_init_data: str = Header(..., alias="X-Telegram-Init-Data")
):
    """
    FastAPI dependency.
    Verifies initData, ensures a User row exists in DB and returns the ORM User instance.
    Raises HTTPException(401) on verification failure.
    """
    try:
        data = verify_telegram_init_data(x_telegram_init_data)
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=str(e)
        )

    user_dict = data.get("user")
    if not user_dict or not isinstance(user_dict, dict):
        raise HTTPException(status_code=401, detail="No user in initData")

    tg_id = user_dict.get("id")
    if tg_id is None:
        raise HTTPException(status_code=401, detail="No user id in initData")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == tg_id).first()
        if not user:
            user = User(
                telegram_id=tg_id,
                balance=10  # initial test balance
            )
            db.add(user)
            db.commit()
            db.refresh(user)
    finally:
        db.close()

    return user

