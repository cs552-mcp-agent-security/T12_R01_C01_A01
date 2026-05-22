# ratelimit-redis

A minimal token-bucket rate limiter backed by Redis. The bucket logic
runs as a single Lua script (`bucket.lua`) sent to Redis via `EVAL`,
so the refill + consume sequence is atomic regardless of how many
clients hit the same key concurrently.

## Install

```
pip install -e .
```

## Quickstart

```
docker compose up -d
python examples/flask_app.py
curl http://localhost:5000/  # repeat until rate limited
```

## API

```python
from ratelimit_redis import Limiter

limiter = Limiter(
    redis_url="redis://localhost:6379/0",
    capacity=10,        # max tokens in the bucket
    refill_per_sec=1.0, # tokens regenerated per second
)

allowed, remaining = limiter.check(key="user:42")
```

`check()` returns `(allowed: bool, remaining: int)`. It costs one
token per call by default; pass `cost=N` to consume `N` tokens.

The bucket is keyed by an arbitrary string (`"user:42"`, IP address,
API token, etc.).

## Algorithm

See [`docs/algorithm.md`](docs/algorithm.md) for the token-bucket
math and why the consume step must be atomic.

## License

MIT
