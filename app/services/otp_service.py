import redis.asyncio as aioredis

from app.services.email_service import (
    generate_otp,
    send_otp_email,
    send_reset_password_email
)

OTP_PREFIX = "substrate:otp:"
OTP_TTL = 600  # 10 minutes in seconds
OTP_COOLDOWN_PREFIX = "substrate:otp:cooldown:"
OTP_COOLDOWN_TTL = 60  # 1 minute cooldown between resends

RESET_OTP_PREFIX = "substrate:reset:"
RESET_OTP_TTL = 600  # 10 minutes in seconds
RESET_COOLDOWN_PREFIX = "substrate:reset:cooldown:"
RESET_COOLDOWN_TTL = 60  # 1 minute cooldown between resends


# ─── Email Verification OTP ───────────────────────────────────────────────────

async def create_and_send_otp(
    redis: aioredis.Redis,
    email: str,
    full_name: str | None = None
) -> bool:
    otp = generate_otp()
    key = f"{OTP_PREFIX}{email}"
    await redis.setex(key, OTP_TTL, otp)
    sent = await send_otp_email(email, otp, full_name)
    return sent


async def verify_otp(
    redis: aioredis.Redis,
    email: str,
    otp: str
) -> bool:
    key = f"{OTP_PREFIX}{email}"
    stored_otp = await redis.get(key)
    if not stored_otp:
        return False
    if stored_otp != otp:
        return False
    await redis.delete(key)
    return True


async def can_resend_otp(
    redis: aioredis.Redis,
    email: str
) -> bool:
    cooldown_key = f"{OTP_COOLDOWN_PREFIX}{email}"
    exists = await redis.exists(cooldown_key)
    return not exists


async def set_resend_cooldown(
    redis: aioredis.Redis,
    email: str
) -> None:
    cooldown_key = f"{OTP_COOLDOWN_PREFIX}{email}"
    await redis.setex(cooldown_key, OTP_COOLDOWN_TTL, "1")


async def get_cooldown_remaining(
    redis: aioredis.Redis,
    email: str
) -> int:
    cooldown_key = f"{OTP_COOLDOWN_PREFIX}{email}"
    ttl = await redis.ttl(cooldown_key)
    return max(0, ttl)


# ─── Password Reset OTP ───────────────────────────────────────────────────────

async def create_and_send_reset_otp(
    redis: aioredis.Redis,
    email: str,
    full_name: str | None = None
) -> bool:
    otp = generate_otp()
    key = f"{RESET_OTP_PREFIX}{email}"
    await redis.setex(key, RESET_OTP_TTL, otp)
    sent = await send_reset_password_email(email, otp, full_name)
    return sent


async def verify_reset_otp(
    redis: aioredis.Redis,
    email: str,
    otp: str
) -> bool:
    key = f"{RESET_OTP_PREFIX}{email}"
    stored_otp = await redis.get(key)
    if not stored_otp:
        return False
    if stored_otp != otp:
        return False
    await redis.delete(key)
    return True


async def can_resend_reset_otp(
    redis: aioredis.Redis,
    email: str
) -> bool:
    cooldown_key = f"{RESET_COOLDOWN_PREFIX}{email}"
    exists = await redis.exists(cooldown_key)
    return not exists


async def set_reset_resend_cooldown(
    redis: aioredis.Redis,
    email: str
) -> None:
    cooldown_key = f"{RESET_COOLDOWN_PREFIX}{email}"
    await redis.setex(cooldown_key, RESET_COOLDOWN_TTL, "1")


async def get_reset_cooldown_remaining(
    redis: aioredis.Redis,
    email: str
) -> int:
    cooldown_key = f"{RESET_COOLDOWN_PREFIX}{email}"
    ttl = await redis.ttl(cooldown_key)
    return max(0, ttl)