
import hashlib
import time
import uuid

from fastapi import HTTPException

from app.config import settings
from app.redis_client import r


def check_rate_limit(key: str) -> None:
    now = time.time()
    window = 60

    key_hash = hashlib.sha256(
        key.encode("utf-8")
    ).hexdigest()

    redis_key = f"rate_limit:{key_hash}"

    request_id = f"{now}:{uuid.uuid4().hex}"

    script = """
    local redis_key = KEYS[1]
    local now = tonumber(ARGV[1])
    local window = tonumber(ARGV[2])
    local limit = tonumber(ARGV[3])
    local request_id = ARGV[4]

    redis.call(
        'ZREMRANGEBYSCORE',
        redis_key,
        '-inf',
        now - window
    )

    local count = redis.call('ZCARD', redis_key)

    if count >= limit then
        return 0
    end

    redis.call(
        'ZADD',
        redis_key,
        now,
        request_id
    )

    redis.call('EXPIRE', redis_key, window)

    return 1
    """

    allowed = r.eval(
        script,
        1,
        redis_key,
        now,
        window,
        settings.rate_limit_per_minute,
        request_id
    )

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": "60"}
        )
