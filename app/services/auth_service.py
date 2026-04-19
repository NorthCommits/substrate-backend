import uuid
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.user import (
    UserRegister, UserLogin, TokenResponse, UserResponse,
    RegisterResponse, VerifyEmailRequest, ResendOtpRequest,
    ForgotPasswordRequest, ResetPasswordRequest
)
from app.services.otp_service import (
    create_and_send_otp, verify_otp,
    can_resend_otp, set_resend_cooldown, get_cooldown_remaining,
    create_and_send_reset_otp, verify_reset_otp,
    can_resend_reset_otp, set_reset_resend_cooldown, get_reset_cooldown_remaining
)
from app.utils.exceptions import (
    EmailAlreadyExistsException, InvalidCredentialsException
)
from fastapi import HTTPException, status


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text


async def register_user(
    db: AsyncSession,
    redis: aioredis.Redis,
    data: UserRegister
) -> RegisterResponse:
    existing = await db.execute(
        select(User).where(User.email == data.email)
    )
    if existing.scalar_one_or_none():
        raise EmailAlreadyExistsException(data.email)

    user = User(
        id=uuid.uuid4(),
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        is_verified=False,
    )
    db.add(user)
    await db.flush()

    base_slug = slugify(data.full_name or data.email.split("@")[0])
    slug = base_slug
    counter = 1
    while True:
        existing_slug = await db.execute(
            select(Workspace).where(Workspace.slug == slug)
        )
        if not existing_slug.scalar_one_or_none():
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    workspace = Workspace(
        id=uuid.uuid4(),
        name=f"{data.full_name or data.email.split('@')[0]}'s Workspace",
        slug=slug,
        owner_id=user.id,
    )
    db.add(workspace)
    await db.flush()

    await create_and_send_otp(redis, data.email, data.full_name)

    return RegisterResponse(
        message="Account created. Please check your email for a verification code.",
        email=data.email
    )


async def verify_email(
    db: AsyncSession,
    redis: aioredis.Redis,
    data: VerifyEmailRequest
) -> TokenResponse:
    result = await db.execute(
        select(User).where(User.email == data.email)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this email"
        )

    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified"
        )

    is_valid = await verify_otp(redis, data.email, data.otp)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code"
        )

    user.is_verified = True
    await db.flush()

    token = create_access_token(subject=str(user.id))

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


async def resend_otp(
    db: AsyncSession,
    redis: aioredis.Redis,
    data: ResendOtpRequest
) -> dict:
    result = await db.execute(
        select(User).where(User.email == data.email)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this email"
        )

    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified"
        )

    allowed = await can_resend_otp(redis, data.email)
    if not allowed:
        remaining = await get_cooldown_remaining(redis, data.email)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {remaining} seconds before requesting a new code"
        )

    await set_resend_cooldown(redis, data.email)
    await create_and_send_otp(redis, data.email, user.full_name)

    return {"message": "A new verification code has been sent to your email"}


async def forgot_password(
    db: AsyncSession,
    redis: aioredis.Redis,
    data: ForgotPasswordRequest
) -> dict:
    result = await db.execute(
        select(User).where(User.email == data.email)
    )
    user = result.scalar_one_or_none()

    # Always return success even if email not found — prevents enumeration
    if not user:
        return {"message": "If an account exists with this email, a reset code has been sent"}

    allowed = await can_resend_reset_otp(redis, data.email)
    if not allowed:
        remaining = await get_reset_cooldown_remaining(redis, data.email)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {remaining} seconds before requesting a new code"
        )

    await set_reset_resend_cooldown(redis, data.email)
    await create_and_send_reset_otp(redis, data.email, user.full_name)

    return {"message": "If an account exists with this email, a reset code has been sent"}


async def reset_password(
    db: AsyncSession,
    redis: aioredis.Redis,
    data: ResetPasswordRequest
) -> dict:
    result = await db.execute(
        select(User).where(User.email == data.email)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this email"
        )

    is_valid = await verify_reset_otp(redis, data.email, data.otp)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset code"
        )

    user.hashed_password = hash_password(data.new_password)
    await db.flush()

    return {"message": "Password reset successfully. You can now log in with your new password."}


async def login_user(
    db: AsyncSession,
    data: UserLogin
) -> TokenResponse:
    result = await db.execute(
        select(User).where(User.email == data.email)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise InvalidCredentialsException()

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in"
        )

    token = create_access_token(subject=str(user.id))

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User:
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()