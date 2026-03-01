from __future__ import annotations

import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from app.core.config import get_settings


class InitDataError(Exception):
    pass


def validate_init_data(init_data: str) -> dict:
    settings = get_settings()
    if not init_data:
        raise InitDataError("Пустой initData")

    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    provided_hash = pairs.pop("hash", None)
    if not provided_hash:
        raise InitDataError("Отсутствует hash")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items(), key=lambda i: i[0]))
    secret_key = hmac.new(b"WebAppData", settings.bot_token.encode("utf-8"), hashlib.sha256).digest()
    generated_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(generated_hash, provided_hash):
        raise InitDataError("Неверная подпись initData")

    auth_date_raw = pairs.get("auth_date")
    if not auth_date_raw:
        raise InitDataError("Отсутствует auth_date")

    auth_date = int(auth_date_raw)
    now = int(time.time())
    if now - auth_date > settings.init_data_max_age_seconds:
        raise InitDataError("initData устарел")

    user_raw = pairs.get("user")
    if not user_raw:
        raise InitDataError("Отсутствует user")

    try:
        user = json.loads(user_raw)
    except json.JSONDecodeError as exc:
        raise InitDataError("Некорректный user JSON") from exc

    return {"user": user, "auth_date": auth_date}
