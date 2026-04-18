import uuid
import secrets
import hashlib

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.models.api_key import ApiKey
from app.schemas.api_key import ApiKeyCreate, ApiKeyCreatedResponse, ApiKeyResponse
from app.utils.exceptions import ApiKeyNotFoundException, InvalidApiKeyException


def generate_raw_key() -> str:
    return f"sk_live_{secrets.token_urlsafe(32)}"


def hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


async def create_api_key(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    data: ApiKeyCreate
) -> ApiKeyCreatedResponse:
    raw_key = generate_raw_key()
    hashed = hash_key(raw_key)
    prefix = raw_key[:16]

    api_key = ApiKey(
        id=uuid.uuid4(),
        name=data.name,
        key_prefix=prefix,
        hashed_key=hashed,
        workspace_id=workspace_id,
    )
    db.add(api_key)
    await db.flush()

    return ApiKeyCreatedResponse(
        id=api_key.id,
        name=api_key.name,
        key_prefix=prefix,
        raw_key=raw_key,
        is_active=api_key.is_active,
        created_at=api_key.created_at,
    )


async def get_workspace_api_keys(
    db: AsyncSession,
    workspace_id: uuid.UUID
) -> list[ApiKey]:
    result = await db.execute(
        select(ApiKey)
        .where(
            ApiKey.workspace_id == workspace_id,
            ApiKey.is_active == True
        )
        .order_by(ApiKey.created_at.desc())
    )
    return list(result.scalars().all())


async def validate_api_key(
    db: AsyncSession,
    raw_key: str
) -> ApiKey:
    hashed = hash_key(raw_key)
    result = await db.execute(
        select(ApiKey)
        .where(
            ApiKey.hashed_key == hashed,
            ApiKey.is_active == True
        )
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise InvalidApiKeyException()

    await db.execute(
        ApiKey.__table__.update()
        .where(ApiKey.id == api_key.id)
        .values(last_used_at=func.now())
    )
    await db.flush()

    return api_key


async def revoke_api_key(
    db: AsyncSession,
    api_key_id: uuid.UUID,
    workspace_id: uuid.UUID
) -> None:
    result = await db.execute(
        select(ApiKey)
        .where(
            ApiKey.id == api_key_id,
            ApiKey.workspace_id == workspace_id
        )
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise ApiKeyNotFoundException(str(api_key_id))
    api_key.is_active = False
    await db.flush()