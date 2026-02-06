import hmac
import hashlib
import json
from urllib.parse import parse_qsl
from app.config import settings


def verify_init_data(init_data: str) -> dict:
    # 1. Парсим initData
    data = dict(parse_qsl(init_data, keep_blank_values=True))

    # 2. Забираем hash
    received_hash = data.pop("hash", None)
    if not received_hash:
        raise ValueError("No hash in initData")

    # 3. Формируем data_check_string (signature ОСТАЁТСЯ)
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(data.items())
    )

    # 4. ПРОМЕЖУТОЧНЫЙ СЕКРЕТ (КРИТИЧЕСКИ ВАЖНО)
    secret_key = hmac.new(
        key=b"WebAppData",
        msg=settings.TG_BOT_TOKEN.encode(),
        digestmod=hashlib.sha256
    ).digest()

    # 5. Финальный hash
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    # 6. Проверка
    if not hmac.compare_digest(calculated_hash, received_hash):
        raise ValueError("Invalid initData signature")

    # 7. Пользователь
    if "user" not in data:
        raise ValueError("No user in initData")

    return json.loads(data["user"])
