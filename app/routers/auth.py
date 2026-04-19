import uuid
import re

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import decode_access_token_async
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.user import UserResponse
from app.utils.exceptions import InvalidTokenException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


router = APIRouter(prefix="/auth", tags=["Auth"])
bearer_scheme = HTTPBearer()


def slugify(text: str) -> str:
    text = text.lower().strip()
    import re
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    token = credentials.credentials
    payload = await decode_access_token_async(token)
    if not payload:
        raise InvalidTokenException()
    return payload.get("sub")


async def get_token_payload(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    token = credentials.credentials
    payload = await decode_access_token_async(token)
    if not payload:
        raise InvalidTokenException()
    return payload


@router.post("/sync", response_model=UserResponse)
async def sync_user(
    payload: dict = Depends(get_token_payload),
    db: AsyncSession = Depends(get_db)
):
    user_id = uuid.UUID(payload.get("sub"))
    email = payload.get("email", "")
    full_name = payload.get("user_metadata", {}).get("full_name")

    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        return existing_user

    user = User(
        id=user_id,
        email=email,
        hashed_password="supabase_managed",
        full_name=full_name,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    await db.flush()

    base_slug = slugify(full_name or email.split("@")[0])
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
        name=f"{full_name or email.split('@')[0]}'s Workspace",
        slug=slug,
        owner_id=user.id,
    )
    db.add(workspace)
    await db.flush()

    return user


@router.get("/me", response_model=UserResponse)
async def me(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(User.id == uuid.UUID(user_id))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise InvalidTokenException()
    return user