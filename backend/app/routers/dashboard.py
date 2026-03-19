from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import structlog
from fastapi import APIRouter, Depends

from app.dependencies import get_current_user, get_db
from app.schemas.dashboard import DashboardStatsResponse
from app.services.dashboard import DashboardService

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession

log = structlog.get_logger()

router = APIRouter()


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    current_user: dict[str, str | int] = Depends(get_current_user),  # noqa: B008
    session: AsyncSession = Depends(get_db),  # noqa: B008
) -> DashboardStatsResponse:
    """Return aggregated dashboard statistics for the authenticated user."""
    service = DashboardService()
    user_id = uuid.UUID(str(current_user["sub"]))
    stats = await service.get_user_stats(session, user_id)
    return DashboardStatsResponse(**stats)
