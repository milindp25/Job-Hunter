from __future__ import annotations

from pydantic import BaseModel


class RecentMatchItem(BaseModel):
    """A single recent match entry for the dashboard."""

    job_title: str
    company: str
    score: int
    matched_at: str | None


class ActivityPoint(BaseModel):
    """Weekly activity data point showing matches and saved jobs."""

    date: str
    matches: int
    saved: int


class DashboardStatsResponse(BaseModel):
    """Aggregated dashboard statistics for the authenticated user."""

    total_saved_jobs: int
    total_matches: int
    resumes_count: int
    avg_match_score: float | None
    avg_ats_score: float | None
    recent_matches: list[RecentMatchItem]
    weekly_activity: list[ActivityPoint]
