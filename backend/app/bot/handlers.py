from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

from app.core.config import get_settings
from app.services.webapp_token import generate_webapp_auth_token

router = Router()


def build_webapp_url(base_url: str, user_id: int) -> str:
    token = generate_webapp_auth_token(user_id)

    parsed = urlparse(base_url)
    query_items = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query_items["auth_token"] = token

    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            urlencode(query_items),
            parsed.fragment,
        )
    )


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    settings = get_settings()

    user_id = message.from_user.id if message.from_user else 0
    webapp_url = build_webapp_url(settings.webapp_url, user_id)

    inline_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть Atomic Habits Mini App",
                    web_app=WebAppInfo(url=webapp_url),
                )
            ]
        ]
    )

    await message.answer(
        (
            "Добро пожаловать. Откройте mini app кнопкой ниже.\n\n"
            "Если Telegram снова не передаст initData, откройте эту же ссылку:\n"
            f"{webapp_url}"
        ),
        reply_markup=inline_keyboard,
    )


@router.message(F.text == "/help")
async def cmd_help(message: Message) -> None:
    await message.answer(
        "Команды:\n/start - открыть mini app\n"
        "Напоминания будут приходить автоматически 1 раз в день."
    )
