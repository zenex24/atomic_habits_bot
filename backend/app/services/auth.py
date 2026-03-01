import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qsl

import jwt
from fastapi import HTTPException, status

from app.config import settings


def verify_telegram_init_data(init_data: str) -> dict:
    if not init_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="init_data is required")
    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    incoming_hash = parsed.pop("hash", "")
    if not incoming_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram data hash")

    check_items = [f"{k}={v}" for k, v in sorted(parsed.items())]
    data_check_string = "\n".join(check_items)
    secret_key = hmac.new(b"WebAppData", settings.telegram_bot_token.encode(), hashlib.sha256).digest()
    local_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if local_hash != incoming_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Telegram auth failed")

    if "user" not in parsed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Telegram user payload is missing")
    return json.loads(parsed["user"])


def create_access_token(payload: dict) -> str:
    exp = datetime.now(UTC) + timedelta(minutes=settings.jwt_exp_minutes)
    body = {**payload, "exp": exp}
    return jwt.encode(body, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
