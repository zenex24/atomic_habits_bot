from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from aiogram.types import BotCommand, MenuButtonWebApp, WebAppInfo

from app.api.routes import router as api_router
from app.bot.instance import bot, dp
from app.bot.setup import register_handlers
from app.core.config import get_settings
from app.db.init_db import init_db, seed_challenges
from app.db.session import SessionLocal, engine
from app.services.reminders import start_scheduler, stop_scheduler

polling_task: asyncio.Task | None = None


def _menu_webapp_url() -> str:
    base_url = settings.webapp_url.strip()
    if not base_url:
        return ""

    parsed = urlparse(base_url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.pop("auth_token", None)
    if settings.public_api_base.strip() and "api_base" not in query:
        query["api_base"] = settings.public_api_base.strip()

    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            urlencode(query),
            parsed.fragment,
        )
    )


async def _configure_bot_ui() -> None:
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Открыть mini app"),
            BotCommand(command="help", description="Помощь"),
        ]
    )

    menu_url = _menu_webapp_url()
    if menu_url:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="Mini App",
                web_app=WebAppInfo(url=menu_url),
            )
        )
        print(f"[startup] Menu button URL set to: {menu_url}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global polling_task

    register_handlers()
    await init_db()
    await _configure_bot_ui()

    async with SessionLocal() as session:
        await seed_challenges(session)

    start_scheduler()
    polling_task = asyncio.create_task(dp.start_polling(bot, handle_signals=False))

    yield

    stop_scheduler()

    if polling_task:
        polling_task.cancel()
        with suppress(asyncio.CancelledError):
            await polling_task

    await bot.session.close()
    await engine.dispose()


settings = get_settings()
app = FastAPI(title="Atomic Habits Bot", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_origin_regex=r"https://.*\.github\.io",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health() -> dict:
    return {"ok": True}


project_root = Path(__file__).resolve().parents[2]
frontend_dir = project_root / "frontend"
app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
