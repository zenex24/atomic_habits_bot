from __future__ import annotations

import hashlib
import hmac
import time

from app.core.config import get_settings


class WebAppTokenError(Exception):
    pass


def _sign_payload(payload: str) -> str:
    settings = get_settings()
    secret = hashlib.sha256(settings.bot_token.encode("utf-8")).digest()
    return hmac.new(secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()


def generate_webapp_auth_token(telegram_user_id: int) -> str:
    ts = int(time.time())
    payload = f"{telegram_user_id}:{ts}"
    sig = _sign_payload(payload)
    return f"{telegram_user_id}:{ts}:{sig}"


def validate_webapp_auth_token(token: str) -> dict:
    settings = get_settings()

    if not token:
        raise WebAppTokenError("Пустой auth token")

    parts = token.split(":")
    if len(parts) != 3:
        raise WebAppTokenError("Некорректный формат auth token")

    user_id_raw, ts_raw, sig = parts
    if not user_id_raw.isdigit() or not ts_raw.isdigit():
        raise WebAppTokenError("Некорректный состав auth token")

    user_id = int(user_id_raw)
    ts = int(ts_raw)

    now = int(time.time())
    if now - ts > settings.init_data_max_age_seconds:
        raise WebAppTokenError("Auth token устарел")

    payload = f"{user_id}:{ts}"
    expected_sig = _sign_payload(payload)
    if not hmac.compare_digest(expected_sig, sig):
        raise WebAppTokenError("Неверная подпись auth token")

    return {
        "user": {
            "id": user_id,
            "username": None,
            "first_name": None,
            "last_name": None,
            "language_code": "ru",
        }
    }
