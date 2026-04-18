from fastapi import APIRouter, Depends
from redis.asyncio import Redis

from app.core.redis import get_redis


router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/")
async def health_check():
    return {
        "status": "ok",
        "service": "Substrate",
        "version": "2.0.0"
    }


@router.get("/redis")
async def redis_health(redis: Redis = Depends(get_redis)):
    try:
        await redis.ping()
        return {
            "status": "ok",
            "redis": "connected"
        }
    except Exception:
        return {
            "status": "error",
            "redis": "disconnected"
        }