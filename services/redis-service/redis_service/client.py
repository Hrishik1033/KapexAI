import os

import redis.asyncio as aioredis

redis = aioredis.from_url(
    os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
    decode_responses=True,
)


async def connect_redis():
    await redis.ping()
    print("Connected to Redis")


async def disconnect_redis():
    await redis.aclose()
    print("Disconnected from Redis")
