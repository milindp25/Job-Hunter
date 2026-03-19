from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy import text

from app.dependencies import get_db

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession

log = structlog.get_logger()

router = APIRouter()


@router.get("/health")
async def health_check(
    session: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict[str, object]:
    """Return application health status with database and Redis checks."""
    checks: dict[str, str] = {}

    # Database connectivity
    try:
        await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        log.error("health_check_db_failed")
        checks["database"] = "error"

    # Redis connectivity (optional — graceful if unconfigured)
    try:
        from app.config import get_settings

        settings = get_settings()
        if settings.REDIS_URL:
            import redis.asyncio as aioredis

            r = aioredis.from_url(settings.REDIS_URL)
            await r.ping()
            await r.aclose()
            checks["redis"] = "ok"
        else:
            checks["redis"] = "not_configured"
    except Exception:
        log.warning("health_check_redis_failed")
        checks["redis"] = "error"

    all_required_ok = all(
        v == "ok" for v in checks.values() if v != "not_configured"
    )
    status = "healthy" if all_required_ok else "degraded"

    return {"status": status, "checks": checks, "version": "1.0.0"}
