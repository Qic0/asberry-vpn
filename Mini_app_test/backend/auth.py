import hmac
import hashlib
import urllib.parse
import json
from typing import Dict

from app.config import settings

BOT_TOKEN = settings.TG_BOT_TOKEN
BOT_TOKEN_BYTES = BOT_TOKEN.encode()


def _parse_init_data(init_data: str) -> Dict[str, str]:
    init_data = urllib.parse.unquote(init_data)
    parsed = urllib.parse.parse_qs(init_data, strict_parsing=True)
    return {k: v[0] for k, v in parsed.items()}


def verify_telegram_init_data(init_data: str) -> Dict:
    if not init_data:
        raise ValueError("Empty initData")

    data = _parse_init_data(init_data)

    if "hash" not in data:
        raise ValueError("No hash in initData")

    received_hash = data.pop("hash")

    check_string = "\n".join(
        f"{k}={v}"
        for k, v in sorted(data.items())
    )

    secret_key = hmac.new(
        b"WebAppData",
        BOT_TOKEN_BYTES,
        hashlib.sha256
    ).digest()

    calculated_hash = hmac.new(
        secret_key,
        check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise ValueError("Invalid initData signature")

    if "user" in data:
        data["user"] = json.loads(data["user"])

    return data

