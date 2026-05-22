"""Token-bucket rate limiter backed by a Redis Lua script."""
from __future__ import annotations

from importlib import resources
from typing import Tuple

import redis


_SCRIPT = resources.files("ratelimit_redis").joinpath("bucket.lua").read_text()


class Limiter:
    def __init__(self, redis_url: str, capacity: int, refill_per_sec: float) -> None:
        self._r = redis.Redis.from_url(redis_url, decode_responses=False)
        self._capacity = capacity
        self._refill = refill_per_sec
        self._sha = self._r.script_load(_SCRIPT)

    def check(self, key: str, cost: int = 1) -> Tuple[bool, int]:
        bucket_key = f"rl:{{{key}}}"  # hash-tag for cluster compatibility
        result = self._r.evalsha(
            self._sha,
            1,
            bucket_key,
            str(self._capacity),
            str(self._refill),
            str(cost),
        )
        allowed = bool(result[0])
        remaining = int(result[1])
        return allowed, remaining
