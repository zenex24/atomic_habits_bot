from datetime import datetime, timezone

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import User
from app.db.session import get_db
from app.services.telegram_auth import InitDataError, validate_init_data


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    x_telegram_init_data: str | None = Header(default=None),
    x_test_user_id: int | None = Header(default=None),
) -> User:
    settings = get_settings()

    if settings.allow_test_auth and x_test_user_id:
        telegram_user = {
            "id": x_test_user_id,
            "username": "test_user",
            "first_name": "Test",
            "last_name": "User",
            "language_code": "ru",
        }
    else:
        try:
            payload = validate_init_data(x_telegram_init_data or "")
        except InitDataError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
        telegram_user = payload["user"]

    telegram_id = int(telegram_user["id"])
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            telegram_id=telegram_id,
            username=telegram_user.get("username"),
            first_name=telegram_user.get("first_name"),
            last_name=telegram_user.get("last_name"),
            display_name=telegram_user.get("first_name"),
            language_code=telegram_user.get("language_code"),
            timezone="UTC",
            reminder_time=settings.default_reminder_time,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        user.username = telegram_user.get("username")
        user.first_name = telegram_user.get("first_name")
        user.last_name = telegram_user.get("last_name")
        user.last_active_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(user)

    return user


def verify_admin_token(admin_token: str | None) -> None:
    if admin_token != get_settings().admin_panel_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
