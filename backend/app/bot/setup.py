from app.bot.handlers import router
from app.bot.instance import dp


def register_handlers() -> None:
    dp.include_router(router)
