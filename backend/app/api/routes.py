import json
from datetime import date, time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.config import settings
from app.db import get_db
from app.models.entities import Challenge, ChallengeKind, ChatMessage, Habit, HabitType, MentorMode, PlanFrequency, PlanItem, User
from app.schemas.dto import (
    ChallengeJoinIn,
    ChatIn,
    ChatOut,
    OnboardingIn,
    ProfilePatchIn,
    TelegramLoginIn,
    TelegramLoginOut,
)
from app.services.auth import create_access_token, verify_telegram_init_data
from app.services.openrouter import build_mentor_system_prompt, chat_completion

router = APIRouter(prefix=settings.api_prefix)


def profile_payload(user: User) -> dict:
    return {
        "name": user.name,
        "timezone": user.timezone,
        "mentor_mode": user.mentor_mode,
        "daily_reminder_time": user.daily_reminder_time.strftime("%H:%M"),
        "onboarding_done": user.onboarding_done,
    }


def challenge_days(kind: str) -> int:
    return {"seven": 7, "fourteen": 14, "thirty": 30, "no_skip": 30}.get(kind, 7)


def ensure_paid_access(user: User) -> None:
    if settings.require_paid_access and not user.is_paid:
        raise HTTPException(status_code=402, detail="Нужна активная подписка")


def template_plan(habits: list[Habit]) -> tuple[list[dict], list[dict]]:
    if not habits:
        return (
            [{"title": "Сделай 1 микро-шаг к новой привычке"}],
            [{"title": "Сделай обзор недели и убери один триггер плохой привычки"}],
        )

    daily = []
    weekly = []
    for habit in habits:
        if habit.type == HabitType.good.value:
            daily.append({"title": f"2 минуты: начать {habit.title.lower()}"})
            weekly.append({"title": f"Подготовить среду для привычки: {habit.title.lower()}"})
        else:
            daily.append({"title": f"Снизить триггер привычки: {habit.title.lower()} на 10%"})
            weekly.append({"title": f"Разобрать причины срывов по привычке: {habit.title.lower()}"})
    return daily[:6], weekly[:6]


@router.post("/auth/telegram-login", response_model=TelegramLoginOut)
async def telegram_login(payload: TelegramLoginIn, db: AsyncSession = Depends(get_db)):
    if payload.init_data and settings.telegram_bot_token:
        tg_user = verify_telegram_init_data(payload.init_data)
        telegram_id = int(tg_user["id"])
        display_name = tg_user.get("first_name", "Пользователь")
    elif settings.allow_local_auth and payload.dev_telegram_id:
        telegram_id = payload.dev_telegram_id
        display_name = payload.dev_name or "Локальный пользователь"
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Telegram auth is required")

    user = await db.scalar(select(User).where(User.telegram_id == telegram_id))
    if not user:
        user = User(
            telegram_id=telegram_id,
            name=display_name,
            timezone=settings.default_timezone,
            is_paid=settings.dev_auto_paid if settings.allow_local_auth and not payload.init_data else False,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    token = create_access_token({"telegram_id": telegram_id})
    return TelegramLoginOut(access_token=token, profile=profile_payload(user))


@router.post("/onboarding")
async def onboarding(
    payload: OnboardingIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user.name = payload.name
    user.mentor_mode = payload.mentor_mode if payload.mentor_mode in MentorMode._value2member_map_ else MentorMode.neutral.value
    user.onboarding_done = True
    await db.execute(delete(Habit).where(Habit.user_id == user.id))

    for title in payload.good_habits:
        db.add(Habit(user_id=user.id, title=title, type=HabitType.good.value, target_mode="build"))
    for title in payload.bad_habits:
        db.add(Habit(user_id=user.id, title=title, type=HabitType.bad.value, target_mode="reduce_to_zero"))
    if payload.other_habit.strip():
        inferred_type = HabitType.bad.value if "брос" in payload.other_habit.lower() else HabitType.good.value
        db.add(
            Habit(
                user_id=user.id,
                title=payload.other_habit.strip(),
                description=payload.details.strip(),
                type=inferred_type,
                is_custom=True,
                target_mode="reduce_to_zero" if inferred_type == HabitType.bad.value else "build",
            )
        )

    await db.commit()
    return {"ok": True}


@router.get("/profile")
async def get_profile(user: User = Depends(get_current_user)):
    return {"profile": profile_payload(user)}


@router.patch("/profile")
async def patch_profile(
    payload: ProfilePatchIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        hh, mm = payload.daily_reminder_time.split(":")
        user.daily_reminder_time = time(hour=int(hh), minute=int(mm))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid time format") from exc

    user.timezone = payload.timezone or settings.default_timezone
    user.mentor_mode = payload.mentor_mode if payload.mentor_mode in MentorMode._value2member_map_ else MentorMode.neutral.value
    await db.commit()
    await db.refresh(user)
    return {"profile": profile_payload(user)}


@router.get("/profile/stats")
async def profile_stats(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    completed_count = await db.scalar(
        select(func.count(Challenge.id)).where(Challenge.user_id == user.id, Challenge.completed.is_(True))
    )
    completion_rate_7d = 72
    return {
        "streak_days": max(1, user.daily_tokens_used // 200) if user.daily_tokens_used else 0,
        "completion_rate_7d": completion_rate_7d,
        "completed_challenges": int(completed_count or 0),
        "level": 1 + (int(completed_count or 0) // 2),
    }


@router.get("/challenges")
async def challenges(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = (await db.scalars(select(Challenge).where(Challenge.user_id == user.id, Challenge.completed.is_(False)))).all()
    return {"items": [{"id": str(c.id), "title": c.title, "current_day": c.current_day, "days_total": c.days_total} for c in rows]}


@router.post("/challenges/join")
async def join_challenge(
    payload: ChallengeJoinIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.kind not in ChallengeKind._value2member_map_:
        raise HTTPException(status_code=400, detail="Unknown challenge kind")
    title_map = {
        "seven": "7 дней подряд",
        "fourteen": "14 дней фокуса",
        "thirty": "30 дней трансформации",
        "no_skip": "Без пропусков",
    }
    challenge = Challenge(
        user_id=user.id,
        kind=payload.kind,
        title=title_map[payload.kind],
        days_total=challenge_days(payload.kind),
        current_day=1,
    )
    db.add(challenge)
    await db.commit()
    return {"ok": True}


@router.get("/plan/daily")
async def daily_plan(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = (await db.scalars(select(PlanItem).where(PlanItem.user_id == user.id, PlanItem.frequency == PlanFrequency.daily.value))).all()
    return {"items": [{"id": str(x.id), "title": x.title} for x in rows]}


@router.get("/plan/weekly")
async def weekly_plan(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = (await db.scalars(select(PlanItem).where(PlanItem.user_id == user.id, PlanItem.frequency == PlanFrequency.weekly.value))).all()
    return {"items": [{"id": str(x.id), "title": x.title} for x in rows]}


@router.post("/plan/generate")
async def generate_plan(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ensure_paid_access(user)
    habits = (await db.scalars(select(Habit).where(Habit.user_id == user.id, Habit.is_active.is_(True)))).all()
    daily_items, weekly_items = template_plan(list(habits))

    prompt = (
        "Сгенерируй JSON {daily:[{title}], weekly:[{title}]} для привычек пользователя в духе Atomic Habits. "
        f"Привычки: {[h.title for h in habits]}"
    )
    ai_data = await chat_completion(
        system_prompt="Ты генерируешь только валидный JSON без markdown.",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=420,
    )
    try:
        parsed = json.loads(ai_data["content"])
        if isinstance(parsed.get("daily"), list) and isinstance(parsed.get("weekly"), list):
            daily_items = [{"title": x["title"]} for x in parsed["daily"] if isinstance(x, dict) and x.get("title")]
            weekly_items = [{"title": x["title"]} for x in parsed["weekly"] if isinstance(x, dict) and x.get("title")]
    except (json.JSONDecodeError, TypeError, ValueError):
        pass

    await db.execute(delete(PlanItem).where(PlanItem.user_id == user.id))
    for item in daily_items[:8]:
        db.add(PlanItem(user_id=user.id, title=item["title"], frequency=PlanFrequency.daily.value))
    for item in weekly_items[:8]:
        db.add(PlanItem(user_id=user.id, title=item["title"], frequency=PlanFrequency.weekly.value))
    await db.commit()
    return {"ok": True, "daily_count": len(daily_items[:8]), "weekly_count": len(weekly_items[:8])}


@router.post("/chat/message", response_model=ChatOut)
async def chat(
    payload: ChatIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ensure_paid_access(user)
    today = date.today()
    if user.daily_token_date != today:
        user.daily_token_date = today
        user.daily_tokens_used = 0
    if user.daily_tokens_used >= settings.max_daily_tokens:
        raise HTTPException(status_code=429, detail="Дневной лимит токенов достигнут")

    history = (
        await db.scalars(select(ChatMessage).where(ChatMessage.user_id == user.id).order_by(ChatMessage.created_at.desc()).limit(8))
    ).all()
    messages = [{"role": msg.role, "content": msg.content} for msg in reversed(history)]
    messages.append({"role": "user", "content": payload.message})

    habits = (await db.scalars(select(Habit).where(Habit.user_id == user.id, Habit.is_active.is_(True)))).all()
    habits_text = ", ".join([h.title for h in habits]) or "не заданы"
    system_prompt = (
        f"{build_mentor_system_prompt(payload.mentor_mode)} "
        f"Текущие привычки пользователя: {habits_text}. "
        "Для плохих привычек веди через постепенное снижение и затем полный отказ."
    )
    result = await chat_completion(system_prompt=system_prompt, messages=messages, max_tokens=500)

    user.daily_tokens_used += result["prompt_tokens"] + result["completion_tokens"]
    db.add(ChatMessage(user_id=user.id, role="user", content=payload.message, prompt_tokens=0, completion_tokens=0))
    db.add(
        ChatMessage(
            user_id=user.id,
            role="assistant",
            content=result["content"],
            prompt_tokens=result["prompt_tokens"],
            completion_tokens=result["completion_tokens"],
        )
    )
    await db.commit()
    return ChatOut(
        answer=result["content"], prompt_tokens=result["prompt_tokens"], completion_tokens=result["completion_tokens"]
    )
