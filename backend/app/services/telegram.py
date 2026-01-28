# app/services/telegram.py
import hmac
import hashlib
from urllib.parse import parse_qsl
from app.config import settings


def verify_init_data(init_data: str) -> dict:
    parsed = dict(parse_qsl(init_data, strict_parsing=True))
    hash_from_tg = parsed.pop("hash")

    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed.items())
    )

    secret_key = hashlib.sha256(
        settings.telegram_bot_token.encode()
    ).digest()

    hmac_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    if hmac_hash != hash_from_tg:
        raise ValueError("Invalid Telegram init data")

    return parsed

