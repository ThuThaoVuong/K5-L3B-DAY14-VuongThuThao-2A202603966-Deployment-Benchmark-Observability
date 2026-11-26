
from datetime import datetime, timezone

from fastapi import HTTPException

from app.config import settings
from app.redis_client import r


PRICE_INPUT_PER_1K = 0.00015
PRICE_OUTPUT_PER_1K = 0.0006


def get_budget_key() -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"daily_budget:{today}"


def check_budget() -> None:
    key = get_budget_key()

    current = float(r.get(key) or 0)

    if current >= settings.daily_budget_usd:
        raise HTTPException(
            status_code=402,
            detail="Daily budget exceeded"
        )


def record_cost(
    input_tokens: int,
    output_tokens: int
) -> float:

    input_cost = (
        input_tokens / 1000
    ) * PRICE_INPUT_PER_1K

    output_cost = (
        output_tokens / 1000
    ) * PRICE_OUTPUT_PER_1K

    total_cost = input_cost + output_cost

    key = get_budget_key()

    pipe = r.pipeline()
    pipe.incrbyfloat(key, total_cost)
    pipe.expire(key, 2 * 24 * 3600)
    pipe.execute()

    return total_cost
