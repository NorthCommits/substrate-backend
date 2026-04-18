import json

import redis.asyncio as aioredis


CONTEXT_CHANNEL_PREFIX = "substrate:context:"


async def publish_context_event(
    redis: aioredis.Redis,
    context_type: str,
    workspace_id: str,
    payload: dict
) -> None:
    channel = f"{CONTEXT_CHANNEL_PREFIX}{workspace_id}:{context_type}"
    await redis.publish(channel, json.dumps(payload))


async def publish_public_context_event(
    redis: aioredis.Redis,
    context_type: str,
    payload: dict
) -> None:
    channel = f"{CONTEXT_CHANNEL_PREFIX}public:{context_type}"
    await redis.publish(channel, json.dumps(payload))


async def subscribe_to_context_type(
    redis: aioredis.Redis,
    context_type: str,
    workspace_id: str
):
    pubsub = redis.pubsub()
    channel = f"{CONTEXT_CHANNEL_PREFIX}{workspace_id}:{context_type}"
    await pubsub.subscribe(channel)
    return pubsub


async def cache_context(
    redis: aioredis.Redis,
    context_id: str,
    payload: dict,
    ttl: int = 300
) -> None:
    key = f"substrate:cache:{context_id}"
    await redis.setex(key, ttl, json.dumps(payload))


async def get_cached_context(
    redis: aioredis.Redis,
    context_id: str
) -> dict | None:
    key = f"substrate:cache:{context_id}"
    data = await redis.get(key)
    if data:
        return json.loads(data)
    return None


async def invalidate_cached_context(
    redis: aioredis.Redis,
    context_id: str
) -> None:
    key = f"substrate:cache:{context_id}"
    await redis.delete(key)