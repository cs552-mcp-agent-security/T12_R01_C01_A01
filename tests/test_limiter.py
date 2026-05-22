import pytest
from ratelimit_redis import Limiter


@pytest.fixture
def limiter():
    return Limiter(
        redis_url="redis://localhost:6379/15",  # test db
        capacity=5,
        refill_per_sec=1.0,
    )


def test_first_call_allowed(limiter):
    allowed, remaining = limiter.check("test:fresh")
    assert allowed
    assert remaining == 4


def test_burst_then_block(limiter):
    for _ in range(5):
        allowed, _ = limiter.check("test:burst")
        assert allowed
    blocked, remaining = limiter.check("test:burst")
    assert not blocked
    assert remaining == 0
