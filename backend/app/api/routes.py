from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, verify_admin_token
from app.api.schemas import (
    AdminMetricsOut,
    AdminUserOut,
    BootstrapResponse,
    ChallengeOut,
    ChatRequest,
    ChatResponse,
    HabitCheckinOut,
    HabitCheckinRequest,
    OnboardingRequest,
    PlanItemCreate,
    PlanItemOut,
    PlanItemUpdate,
    ProfileOut,
    ProfileUpdateRequest,
)
from app.core.config import get_settings
from app.db.models import Challenge, ChatMessage, HabitLog, PlanItem, User, UserChallenge
from app.db.session import get_db
from app.services.analytics import get_admin_metrics
from app.services.coach import ask_openrouter

router = APIRouter(prefix="/api", tags=["api"])


def _safe_tz(tz_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def _local_date_for_user(user: User) -> date:
    return datetime.now(tz=ZoneInfo("UTC")).astimezone(_safe_tz(user.timezone)).date()


async def _recompute_streak(db: AsyncSession, user: User, current_date: date) -> tuple[int, int]:
    result = await db.execute(
        select(HabitLog.log_date)
        .where(and_(HabitLog.user_id == user.id, HabitLog.completed.is_(True)))
        .order_by(desc(HabitLog.log_date))
    )
    dates = [row[0] for row in result.all()]
    if not dates:
        user.streak_days = 0
        return 0, user.best_streak

    dates_set = set(dates)
    streak = 0
    cursor = current_date

    while cursor in dates_set:
        streak += 1
        cursor = cursor - timedelta(days=1)

    user.streak_days = streak
    if streak > user.best_streak:
        user.best_streak = streak

    await db.commit()
    await db.refresh(user)
    return user.streak_days, user.best_streak


async def _home_payload(db: AsyncSession, user: User) -> dict:
    today = _local_date_for_user(user)

    today_log_result = await db.execute(
        select(HabitLog).where(and_(HabitLog.user_id == user.id, HabitLog.log_date == today))
    )
    today_log = today_log_result.scalar_one_or_none()
    has_today_done = bool(today_log and today_log.completed)

    plan_count = await db.scalar(select(func.count(PlanItem.id)).where(PlanItem.user_id == user.id)) or 0
    done_count = (
        await db.scalar(
            select(func.count(PlanItem.id)).where(and_(PlanItem.user_id == user.id, PlanItem.is_done.is_(True)))
        )
        or 0
    )

    active_challenges = (
        await db.scalar(
            select(func.count(UserChallenge.id)).where(
                and_(UserChallenge.user_id == user.id, UserChallenge.is_completed.is_(False))
            )
        )
        or 0
    )

    return {
        "habit_name": user.habit_name,
        "goal_type": user.goal_type,
        "streak_days": user.streak_days,
        "best_streak": user.best_streak,
        "today_done": has_today_done,
        "plan_progress": {"done": int(done_count), "total": int(plan_count)},
        "active_challenges": int(active_challenges),
    }


@router.get("/privacy")
async def get_privacy() -> dict:
    return {
        "title": "Политика конфиденциальности",
        "text": (
            "Мы обрабатываем данные профиля привычек, историю прогресса и переписку с наставником "
            "для персонализации рекомендаций. Данные не передаются третьим лицам кроме технических "
            "провайдеров инфраструктуры и LLM API (OpenRouter) для генерации ответов."
        ),
    }


@router.get("/bootstrap", response_model=BootstrapResponse)
async def bootstrap(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> BootstrapResponse:
    return BootstrapResponse(
        user={
            "telegram_id": user.telegram_id,
            "display_name": user.display_name,
            "timezone": user.timezone,
            "mentor_tone": user.mentor_tone,
        },
        onboarding_completed=user.onboarding_completed,
        home=await _home_payload(db, user),
    )


@router.post("/onboarding")
async def complete_onboarding(
    payload: OnboardingRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if not payload.privacy_accepted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Нужно согласие с политикой")

    user.display_name = payload.display_name
    user.goal_type = payload.goal_type
    user.habit_category = payload.habit_category
    user.habit_name = payload.habit_name
    user.habit_details = payload.habit_details
    user.motivation = payload.motivation
    user.baseline_frequency = payload.baseline_frequency
    user.mentor_tone = payload.mentor_tone
    user.reminder_time = payload.reminder_time
    user.timezone = payload.timezone
    user.privacy_accepted = payload.privacy_accepted
    user.privacy_accepted_at = datetime.now(tz=ZoneInfo("UTC"))
    user.onboarding_completed = True

    await db.commit()

    existing_plan = await db.scalar(select(func.count(PlanItem.id)).where(PlanItem.user_id == user.id)) or 0
    if existing_plan == 0:
        defaults = [
            PlanItem(
                user_id=user.id,
                title="Минимальное действие на сегодня",
                description="Сделайте версию привычки, которая занимает не больше 2 минут.",
            ),
            PlanItem(
                user_id=user.id,
                title="Якорь привычки",
                description="Привяжите действие к уже существующему ритуалу (после/перед).",
            ),
            PlanItem(
                user_id=user.id,
                title="Подготовка окружения",
                description="Сделайте полезную привычку очевидной, вредную - труднодоступной.",
            ),
        ]
        db.add_all(defaults)
        await db.commit()

    return {"ok": True}


@router.get("/home")
async def get_home(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> dict:
    return await _home_payload(db, user)


@router.get("/plan", response_model=list[PlanItemOut])
async def get_plan(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> list[PlanItemOut]:
    result = await db.execute(select(PlanItem).where(PlanItem.user_id == user.id).order_by(PlanItem.created_at.asc()))
    rows = result.scalars().all()
    return [
        PlanItemOut(
            id=item.id,
            title=item.title,
            description=item.description,
            weekday=item.weekday,
            is_done=item.is_done,
        )
        for item in rows
    ]


@router.post("/plan/items", response_model=PlanItemOut)
async def create_plan_item(
    payload: PlanItemCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PlanItemOut:
    item = PlanItem(
        user_id=user.id,
        title=payload.title,
        description=payload.description,
        weekday=payload.weekday,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)

    return PlanItemOut(
        id=item.id,
        title=item.title,
        description=item.description,
        weekday=item.weekday,
        is_done=item.is_done,
    )


@router.patch("/plan/items/{item_id}", response_model=PlanItemOut)
async def update_plan_item(
    item_id: int,
    payload: PlanItemUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PlanItemOut:
    result = await db.execute(select(PlanItem).where(and_(PlanItem.id == item_id, PlanItem.user_id == user.id)))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пункт плана не найден")

    item.is_done = payload.is_done
    item.done_at = datetime.now(tz=ZoneInfo("UTC")) if payload.is_done else None
    await db.commit()
    await db.refresh(item)

    return PlanItemOut(
        id=item.id,
        title=item.title,
        description=item.description,
        weekday=item.weekday,
        is_done=item.is_done,
    )


@router.delete("/plan/items/{item_id}")
async def delete_plan_item(item_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(select(PlanItem).where(and_(PlanItem.id == item_id, PlanItem.user_id == user.id)))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пункт плана не найден")

    await db.delete(item)
    await db.commit()
    return {"ok": True}


@router.post("/plan/checkin", response_model=HabitCheckinOut)
async def checkin_habit(
    payload: HabitCheckinRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HabitCheckinOut:
    local_date = _local_date_for_user(user)

    result = await db.execute(
        select(HabitLog).where(and_(HabitLog.user_id == user.id, HabitLog.log_date == local_date))
    )
    log = result.scalar_one_or_none()
    if log is None:
        log = HabitLog(user_id=user.id, log_date=local_date, completed=payload.completed, note=payload.note)
        db.add(log)
    else:
        log.completed = payload.completed
        log.note = payload.note

    await db.commit()

    streak_days, best_streak = await _recompute_streak(db, user, local_date)
    return HabitCheckinOut(streak_days=streak_days, best_streak=best_streak, log_date=local_date)


@router.get("/challenges", response_model=list[ChallengeOut])
async def list_challenges(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> list[ChallengeOut]:
    result = await db.execute(select(Challenge).where(Challenge.is_active.is_(True)).order_by(Challenge.id.asc()))
    challenges = result.scalars().all()

    user_result = await db.execute(select(UserChallenge).where(UserChallenge.user_id == user.id))
    user_links = {row.challenge_id: row for row in user_result.scalars().all()}

    return [
        ChallengeOut(
            id=challenge.id,
            title=challenge.title,
            description=challenge.description,
            duration_days=challenge.duration_days,
            points=challenge.points,
            joined=challenge.id in user_links,
            progress_days=user_links[challenge.id].progress_days if challenge.id in user_links else 0,
            is_completed=user_links[challenge.id].is_completed if challenge.id in user_links else False,
        )
        for challenge in challenges
    ]


@router.post("/challenges/{challenge_id}/join")
async def join_challenge(
    challenge_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    challenge = await db.get(Challenge, challenge_id)
    if challenge is None or not challenge.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Челлендж не найден")

    existing = await db.execute(
        select(UserChallenge).where(and_(UserChallenge.user_id == user.id, UserChallenge.challenge_id == challenge_id))
    )
    link = existing.scalar_one_or_none()
    if link is None:
        link = UserChallenge(user_id=user.id, challenge_id=challenge_id)
        db.add(link)
        await db.commit()

    return {"ok": True}


@router.post("/challenges/{challenge_id}/progress")
async def challenge_progress(
    challenge_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(UserChallenge).where(and_(UserChallenge.user_id == user.id, UserChallenge.challenge_id == challenge_id))
    )
    link = result.scalar_one_or_none()
    if link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Сначала вступите в челлендж")

    if link.is_completed:
        return {"ok": True, "completed": True, "progress_days": link.progress_days}

    challenge = await db.get(Challenge, challenge_id)
    link.progress_days += 1
    if challenge and link.progress_days >= challenge.duration_days:
        link.is_completed = True
        link.completed_at = datetime.now(tz=ZoneInfo("UTC"))

    await db.commit()
    return {"ok": True, "completed": link.is_completed, "progress_days": link.progress_days}


@router.get("/profile", response_model=ProfileOut)
async def get_profile(user: User = Depends(get_current_user)) -> ProfileOut:
    return ProfileOut(
        display_name=user.display_name,
        mentor_tone=user.mentor_tone,
        reminder_time=user.reminder_time,
        timezone=user.timezone,
        goal_type=user.goal_type,
        habit_name=user.habit_name,
        habit_category=user.habit_category,
        habit_details=user.habit_details,
        motivation=user.motivation,
        baseline_frequency=user.baseline_frequency,
        streak_days=user.streak_days,
        best_streak=user.best_streak,
    )


@router.patch("/profile")
async def update_profile(
    payload: ProfileUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if payload.display_name is not None:
        user.display_name = payload.display_name
    if payload.mentor_tone is not None:
        user.mentor_tone = payload.mentor_tone
    if payload.reminder_time is not None:
        user.reminder_time = payload.reminder_time
    if payload.timezone is not None:
        user.timezone = payload.timezone
    if payload.habit_details is not None:
        user.habit_details = payload.habit_details

    await db.commit()
    return {"ok": True}


@router.post("/chat", response_model=ChatResponse)
async def chat_with_mentor(
    payload: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    settings = get_settings()
    local_today = _local_date_for_user(user)

    if user.message_count_date != local_today:
        user.message_count_date = local_today
        user.message_count_today = 0

    if user.message_count_today >= settings.daily_chat_limit:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Лимит сообщений на сегодня исчерпан")

    history_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.user_id == user.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(12)
    )
    history_rows = list(reversed(history_result.scalars().all()))
    history = [{"role": row.role, "content": row.content} for row in history_rows]

    profile = {
        "display_name": user.display_name,
        "goal_type": user.goal_type,
        "habit_name": user.habit_name,
        "habit_category": user.habit_category,
        "habit_details": user.habit_details,
        "motivation": user.motivation,
        "mentor_tone": user.mentor_tone,
    }

    reply = await ask_openrouter(profile, history, payload.message)

    db.add(ChatMessage(user_id=user.id, role="user", content=payload.message, model=settings.openrouter_model))
    db.add(ChatMessage(user_id=user.id, role="assistant", content=reply, model=settings.openrouter_model))
    user.message_count_today += 1

    await db.commit()

    return ChatResponse(reply=reply, remaining_today=settings.daily_chat_limit - user.message_count_today)


@router.get("/admin/metrics", response_model=AdminMetricsOut)
async def admin_metrics(
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> AdminMetricsOut:
    verify_admin_token(token)
    metrics = await get_admin_metrics(db)
    return AdminMetricsOut(**metrics)


@router.get("/admin/users", response_model=list[AdminUserOut])
async def admin_users(token: str = Query(...), db: AsyncSession = Depends(get_db)) -> list[AdminUserOut]:
    verify_admin_token(token)

    result = await db.execute(select(User).order_by(User.created_at.desc()).limit(300))
    users = result.scalars().all()

    return [
        AdminUserOut(
            telegram_id=user.telegram_id,
            display_name=user.display_name,
            goal_type=user.goal_type,
            habit_name=user.habit_name,
            onboarding_completed=user.onboarding_completed,
            streak_days=user.streak_days,
            last_active_at=user.last_active_at.isoformat() if user.last_active_at else "",
        )
        for user in users
    ]
