from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import structlog
from sqlalchemy import func
from sqlmodel import select

from app.models.ats_check import AtsCheck
from app.models.job import Job, SavedJob
from app.models.job_match import JobMatch
from app.models.resume import Resume

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

log = structlog.get_logger()


class DashboardService:
    """Aggregates user dashboard statistics from multiple models."""

    async def get_user_stats(
        self, session: AsyncSession, user_id: uuid.UUID
    ) -> dict[str, object]:
        """Fetch aggregated dashboard stats for a given user.

        Returns counts, averages, recent matches, and weekly activity data.
        """
        log.info("dashboard_stats_requested", user_id=str(user_id))

        # Counts
        saved_jobs_count = await self._count(
            session, select(func.count(SavedJob.id)).where(SavedJob.user_id == user_id)
        )
        matches_count = await self._count(
            session, select(func.count(JobMatch.id)).where(JobMatch.user_id == user_id)
        )
        resumes_count = await self._count(
            session, select(func.count(Resume.id)).where(Resume.user_id == user_id)
        )

        # Average match score
        avg_match_result = await session.execute(
            select(func.avg(JobMatch.overall_score)).where(JobMatch.user_id == user_id)
        )
        avg_match_score = avg_match_result.scalar()

        # Average ATS score
        avg_ats_result = await session.execute(
            select(func.avg(AtsCheck.overall_score)).where(AtsCheck.user_id == user_id)
        )
        avg_ats_score = avg_ats_result.scalar()

        # Recent matches (top 5 with job details)
        recent_matches = await self._get_recent_matches(session, user_id)

        # Weekly activity (last 4 weeks)
        weekly_activity = await self._get_weekly_activity(session, user_id)

        return {
            "total_saved_jobs": saved_jobs_count,
            "total_matches": matches_count,
            "resumes_count": resumes_count,
            "avg_match_score": round(float(avg_match_score), 1) if avg_match_score else None,
            "avg_ats_score": round(float(avg_ats_score), 1) if avg_ats_score else None,
            "recent_matches": recent_matches,
            "weekly_activity": weekly_activity,
        }

    async def _get_recent_matches(
        self, session: AsyncSession, user_id: uuid.UUID
    ) -> list[dict[str, object]]:
        """Return last 5 job matches with associated job details."""
        stmt = (
            select(JobMatch)
            .where(JobMatch.user_id == user_id)
            .order_by(JobMatch.created_at.desc())  # type: ignore[union-attr]
            .limit(5)
        )
        result = await session.execute(stmt)
        matches = result.scalars().all()

        recent_items: list[dict[str, object]] = []
        for match in matches:
            job_result = await session.execute(
                select(Job).where(Job.id == match.job_id)
            )
            job = job_result.scalar_one_or_none()
            if job:
                recent_items.append({
                    "job_title": job.title,
                    "company": job.company,
                    "score": match.overall_score,
                    "matched_at": match.created_at.isoformat() if match.created_at else None,
                })

        return recent_items

    async def _get_weekly_activity(
        self, session: AsyncSession, user_id: uuid.UUID
    ) -> list[dict[str, object]]:
        """Return match and saved-job counts for each of the last 4 weeks."""
        now = datetime.now(UTC)
        weekly: list[dict[str, object]] = []

        for week_offset in range(4):
            week_start = now - timedelta(weeks=3 - week_offset)
            week_end = week_start + timedelta(weeks=1)

            matches_week = await self._count(
                session,
                select(func.count(JobMatch.id)).where(
                    JobMatch.user_id == user_id,
                    JobMatch.created_at >= week_start,
                    JobMatch.created_at < week_end,
                ),
            )
            saved_week = await self._count(
                session,
                select(func.count(SavedJob.id)).where(
                    SavedJob.user_id == user_id,
                    SavedJob.saved_at >= week_start,
                    SavedJob.saved_at < week_end,
                ),
            )
            weekly.append({
                "date": week_start.strftime("%b %d"),
                "matches": matches_week,
                "saved": saved_week,
            })

        return weekly

    async def _count(self, session: AsyncSession, stmt: object) -> int:
        """Execute a count query and return the scalar result."""
        result = await session.execute(stmt)  # type: ignore[arg-type]
        return result.scalar() or 0
