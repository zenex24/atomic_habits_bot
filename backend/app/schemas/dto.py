from pydantic import BaseModel, Field


class TelegramLoginIn(BaseModel):
    init_data: str = ""
    dev_telegram_id: int | None = None
    dev_name: str | None = None


class ProfileOut(BaseModel):
    name: str
    timezone: str
    mentor_mode: str
    daily_reminder_time: str
    onboarding_done: bool


class TelegramLoginOut(BaseModel):
    access_token: str
    profile: ProfileOut


class OnboardingIn(BaseModel):
    name: str = Field(min_length=2, max_length=60)
    good_habits: list[str] = Field(default_factory=list)
    bad_habits: list[str] = Field(default_factory=list)
    other_habit: str = Field(default="", max_length=300)
    details: str = Field(default="", max_length=500)
    mentor_mode: str = Field(default="neutral")


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=1200)
    mentor_mode: str = "neutral"


class ChatOut(BaseModel):
    answer: str
    prompt_tokens: int = 0
    completion_tokens: int = 0


class ChallengeJoinIn(BaseModel):
    kind: str


class ProfilePatchIn(BaseModel):
    daily_reminder_time: str
    timezone: str
    mentor_mode: str
