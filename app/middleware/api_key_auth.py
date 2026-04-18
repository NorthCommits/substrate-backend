import uuid

from fastapi import Depends, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.api_key import ApiKey
from app.models.workspace import Workspace
from app.services.api_key_service import validate_api_key
from app.services.workspace_service import get_workspace_by_id
from app.utils.exceptions import InvalidApiKeyException


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_workspace_from_api_key(
    api_key: str = Security(api_key_header),
    db: AsyncSession = Depends(get_db)
) -> Workspace:
    if not api_key:
        raise InvalidApiKeyException()

    validated_key = await validate_api_key(db, api_key)
    workspace = await get_workspace_by_id(db, validated_key.workspace_id)
    return workspace


async def get_api_key_record(
    api_key: str = Security(api_key_header),
    db: AsyncSession = Depends(get_db)
) -> ApiKey:
    if not api_key:
        raise InvalidApiKeyException()

    return await validate_api_key(db, api_key)