import os

from upstash_redis import Redis

redis = Redis(
    url=os.environ["UPSTASH_REDIS_REST_URL"],
    token=os.environ["UPSTASH_REDIS_REST_TOKEN"],
)


def connect_redis():
    redis.ping()
    print("Connected to Redis")


def disconnect_redis():
    print("Redis client closed")
