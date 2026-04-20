from typing import Any
import httpx
from jose import jwt, JWTError
from app.core.config import settings

JWKS_URL = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
_jwks_cache = None


async def get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache:
        return _jwks_cache
    async with httpx.AsyncClient() as client:
        response = await client.get(JWKS_URL)
        _jwks_cache = response.json()
    return _jwks_cache


async def decode_access_token_async(token: str) -> dict[str, Any] | None:
    try:
        jwks = await get_jwks()
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["ES256", "RS256", "HS256"],
            options={"verify_aud": False}
        )
        return payload
    except Exception as e:
        print(f"JWT decode error: {e}")
        return None


def decode_access_token(token: str) -> dict[str, Any] | None:
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, decode_access_token_async(token))
                return future.result()
        return loop.run_until_complete(decode_access_token_async(token))
    except Exception as e:
        print(f"Token decode fallback error: {e}")
        return None