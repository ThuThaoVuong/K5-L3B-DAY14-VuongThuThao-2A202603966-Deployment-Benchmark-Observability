
import json
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request
)
from pydantic import BaseModel, Field

from app.auth import verify_api_key
from app.config import settings
from app.cost_guard import check_budget, record_cost
from app.rate_limiter import check_rate_limit
from app.redis_client import redis_healthy
from utils.mock_llm import ask as llm_ask


# =========================
# Structured JSON Logging
# =========================

class JsonFormatter(logging.Formatter):

    def format(self, record):
        log_data = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "lvl": record.levelname,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(
                record.exc_info
            )

        return json.dumps(log_data, ensure_ascii=False)


handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())

logger = logging.getLogger("agent")
logger.setLevel(logging.INFO)
logger.handlers.clear()
logger.addHandler(handler)
logger.propagate = False


# =========================
# Graceful Shutdown
# =========================

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Agent started")
    yield
    logger.info("Agent shutting down")


app = FastAPI(
    title="Production AI Agent",
    lifespan=lifespan
)


# =========================
# Request Model
# =========================

class AskRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000
    )
    user_id: str = "default"


# =========================
# Request Logging
# =========================

@app.middleware("http")
async def observe_requests(request: Request, call_next):
    start = time.time()

    response = await call_next(request)

    elapsed = round(
        (time.time() - start) * 1000,
        2
    )

    logger.info(json.dumps({
        "event": "request",
        "path": request.url.path,
        "method": request.method,
        "status": response.status_code,
        "ms": elapsed
    }))

    return response


# =========================
# Health Checks
# =========================

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "environment": settings.environment
    }


@app.get("/ready")
def ready():
    if not redis_healthy():
        raise HTTPException(
            status_code=503,
            detail="Redis is unavailable"
        )

    return {
        "status": "ready",
        "redis": "connected"
    }


# =========================
# AI Agent
# =========================

@app.post("/ask")
def ask(
    body: AskRequest,
    api_key: str = Depends(verify_api_key)
):
    # Step 1: Rate limiting
    check_rate_limit(api_key)

    # Step 2: Check budget
    check_budget()

    # Step 3: Call mock LLM
    answer = llm_ask(body.question)

    # Step 4: Estimate token usage
    input_tokens = max(
        1, len(body.question) // 4
    )

    output_tokens = max(
        1, len(answer) // 4
    )

    # Step 5: Record cost
    cost = record_cost(
        input_tokens,
        output_tokens
    )

    logger.info(json.dumps({
        "event": "agent_request",
        "user_id": body.user_id,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": cost
    }))

    return {
        "question": body.question,
        "answer": answer,
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost
        }
    }
