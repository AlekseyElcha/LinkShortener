from redis.asyncio import Redis
from functools import lru_cache
from time import time
import random

@lru_cache
def get_redis():
    return Redis(host="localhost", port=6379)

class RateLimiter:
    def __init__(self, redis: Redis):
        self.redis = redis


    async def is_limited(
            self,
            ip_address: str,
            endpoint: str,
            max_requests: int,
            window_seconds: int,
    ):
        key = f"rate_limiter:{endpoint}:{ip_address}"

        current_ms = time() * 1000
        window_start_ms = current_ms - window_seconds*1000

        current_request = f"{current_ms}-{random.randint(0, 100000)}"


        async with self.redis.pipeline(transaction=True) as pipe:
            await pipe.zremrangebyscore(key, 0, window_start_ms)

            await pipe.zcard(key)

            await pipe.zadd(key, {current_request: current_ms})

            await pipe.expire(key, window_seconds)

            res = await pipe.execute()

        _, current_count, _, _ = res
        return current_count >= max_requests

@lru_cache
def get_rate_limiter():
    return RateLimiter(get_redis())