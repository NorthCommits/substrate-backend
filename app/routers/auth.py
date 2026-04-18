from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.schemas.user import UserRegister, UserLogin, TokenResponse, UserResponse
from app.services import auth_service
from app.utils.exceptions import InvalidTokenException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


router = APIRouter(prefix="/auth", tags=["Auth"])
bearer_scheme = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db)
) -> str:
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise InvalidTokenException()
    return payload.get("sub")


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    data: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    return await auth_service.register_user(db, data)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    return await auth_service.login_user(db, data)


@router.get("/me", response_model=UserResponse)
async def me(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    import uuid
    user = await auth_service.get_user_by_id(db, uuid.UUID(user_id))
    if not user:
        raise InvalidTokenException()
    return user