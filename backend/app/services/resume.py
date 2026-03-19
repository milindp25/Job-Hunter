from __future__ import annotations

import pathlib
import uuid
from typing import TYPE_CHECKING

import structlog
from sqlmodel import func, select

from app.exceptions import (
    FileTooLargeError,
    InvalidFileTypeError,
    ResumeLimitExceededError,
    ResumeNotFoundError,
    ResumeUploadError,
)
from app.models.resume import Resume
from app.services import ats_checker
from app.services.resume_parser import parse_resume
from app.services.storage import get_storage

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession

log = structlog.get_logger()

_MAX_RESUME_SIZE = 5 * 1024 * 1024  # 5 MB
_MAX_RESUMES_PER_USER = 10
_ALLOWED_EXTENSIONS = {".pdf", ".docx"}
_CONTENT_TYPES: dict[str, str] = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


async def upload_resume(
    session: AsyncSession,
    user_id: str,
    file_content: bytes,
    filename: str,
) -> Resume:
    """Upload, parse, and store a resume file.

    Validates file type, size, and per-user resume limit before uploading
    to object storage and persisting the record.

    Args:
        session: Async database session.
        user_id: ID of the owning user.
        file_content: Raw bytes of the uploaded file.
        filename: Original filename (used for extension detection).

    Returns:
        The newly created Resume model instance.

    Raises:
        InvalidFileTypeError: If the file extension is not PDF or DOCX.
        FileTooLargeError: If file_content exceeds 5 MB.
        ResumeLimitExceededError: If the user already has 10 resumes.
        ResumeUploadError: If object-storage upload fails.
    """
    # 1. Validate extension
    extension = pathlib.PurePosixPath(filename).suffix.lower()
    if extension not in _ALLOWED_EXTENSIONS:
        log.warning("invalid_file_type", filename=filename, extension=extension)
        raise InvalidFileTypeError()

    # 2. Validate size
    if len(file_content) > _MAX_RESUME_SIZE:
        log.warning(
            "file_too_large",
            filename=filename,
            size=len(file_content),
            max_size=_MAX_RESUME_SIZE,
        )
        raise FileTooLargeError()

    # 3. Check per-user resume count
    count_statement = (
        select(func.count())
        .select_from(Resume)
        .where(Resume.user_id == uuid.UUID(user_id))
    )
    count_result = await session.exec(count_statement)
    existing_count: int = count_result.one()
    if existing_count >= _MAX_RESUMES_PER_USER:
        log.warning("resume_limit_exceeded", user_id=user_id, count=existing_count)
        raise ResumeLimitExceededError()

    # 4. Determine file_type and content_type
    file_type = extension.lstrip(".")
    content_type = _CONTENT_TYPES[extension]

    # 5. Generate storage key
    storage_key = f"resumes/{user_id}/{uuid.uuid4()}_{filename}"

    # 6. Upload to R2
    try:
        await get_storage().upload_file(storage_key, file_content, content_type)
    except Exception:
        log.exception("resume_upload_failed", storage_key=storage_key)
        raise ResumeUploadError() from None

    # 7. Parse the resume
    parsed = await parse_resume(file_content, filename)
    raw_text: str = parsed["raw_text"]

    # Build parsed_data dict without raw_text (stored separately)
    parsed_data: dict[str, str | None | list[str] | list[dict[str, str | None]]] = {
        "full_name": parsed["full_name"],
        "email": parsed["email"],
        "phone": parsed["phone"],
        "location": parsed["location"],
        "summary": parsed["summary"],
        "skills": parsed["skills"],
        "experience": parsed["experience"],
        "education": parsed["education"],
        "certifications": parsed["certifications"],
    }

    # 8. First resume becomes primary
    is_primary = existing_count == 0

    # 9. Create model and persist
    resume = Resume(
        user_id=uuid.UUID(user_id),
        filename=filename,
        file_size=len(file_content),
        file_type=file_type,
        storage_key=storage_key,
        raw_text=raw_text,
        parsed_data=parsed_data,
        is_primary=is_primary,
    )
    session.add(resume)
    await session.flush()

    # Auto-run ATS format check (never fail the upload if this fails)
    try:
        await ats_checker.run_format_check(session, resume)
    except Exception:
        log.warning(
            "ats_format_check_on_upload_failed",
            resume_id=str(resume.id),
            user_id=user_id,
        )

    log.info(
        "resume_uploaded",
        resume_id=str(resume.id),
        user_id=user_id,
        filename=filename,
        is_primary=is_primary,
    )
    return resume


async def get_resumes(
    session: AsyncSession,
    user_id: str,
) -> list[Resume]:
    """Get all resumes for a user, ordered by most recent first.

    Args:
        session: Async database session.
        user_id: ID of the owning user.

    Returns:
        List of Resume instances (may be empty).
    """
    statement = (
        select(Resume)
        .where(Resume.user_id == uuid.UUID(user_id))
        .order_by(Resume.created_at.desc())  # type: ignore[union-attr]
    )
    result = await session.exec(statement)
    resumes = list(result.all())
    log.info("resumes_listed", user_id=user_id, count=len(resumes))
    return resumes


async def get_resume(
    session: AsyncSession,
    user_id: str,
    resume_id: str,
) -> Resume:
    """Get a single resume by ID, scoped to the owning user.

    Args:
        session: Async database session.
        user_id: ID of the owning user (for authorization).
        resume_id: ID of the resume.

    Returns:
        The matching Resume instance.

    Raises:
        ResumeNotFoundError: If the resume does not exist or belongs to another user.
    """
    statement = select(Resume).where(
        Resume.id == uuid.UUID(resume_id),
        Resume.user_id == uuid.UUID(user_id),
    )
    result = await session.exec(statement)
    resume = result.first()
    if resume is None:
        log.warning("resume_not_found", user_id=user_id, resume_id=resume_id)
        raise ResumeNotFoundError()
    return resume


async def delete_resume(
    session: AsyncSession,
    user_id: str,
    resume_id: str,
) -> None:
    """Delete a resume and its stored file.

    If the deleted resume was primary, the next most recent resume is
    promoted to primary.

    Args:
        session: Async database session.
        user_id: ID of the owning user.
        resume_id: ID of the resume to delete.

    Raises:
        ResumeNotFoundError: If the resume does not exist or belongs to another user.
    """
    resume = await get_resume(session, user_id, resume_id)

    # Delete from R2 (best-effort -- log warning but do not block DB deletion)
    try:
        await get_storage().delete_file(resume.storage_key)
    except Exception:
        log.warning(
            "resume_storage_delete_failed",
            storage_key=resume.storage_key,
            resume_id=resume_id,
        )

    was_primary = resume.is_primary

    await session.delete(resume)
    await session.flush()

    # Promote next most recent resume if the deleted one was primary
    if was_primary:
        promote_statement = (
            select(Resume)
            .where(
                Resume.user_id == uuid.UUID(user_id),
                Resume.id != uuid.UUID(resume_id),
            )
            .order_by(Resume.created_at.desc())  # type: ignore[union-attr]
        )
        promote_result = await session.exec(promote_statement)
        next_resume = promote_result.first()
        if next_resume is not None:
            next_resume.is_primary = True
            session.add(next_resume)
            await session.flush()
            log.info(
                "resume_primary_promoted",
                user_id=user_id,
                promoted_resume_id=str(next_resume.id),
            )

    log.info("resume_deleted", user_id=user_id, resume_id=resume_id)


async def set_primary_resume(
    session: AsyncSession,
    user_id: str,
    resume_id: str,
) -> Resume:
    """Set a resume as the user's primary resume.

    Unsets is_primary on all other resumes for the user first.

    Args:
        session: Async database session.
        user_id: ID of the owning user.
        resume_id: ID of the resume to mark as primary.

    Returns:
        The updated Resume instance with is_primary=True.

    Raises:
        ResumeNotFoundError: If the resume does not exist or belongs to another user.
    """
    target = await get_resume(session, user_id, resume_id)

    # Unset is_primary on all user's resumes
    all_statement = select(Resume).where(Resume.user_id == uuid.UUID(user_id))
    all_result = await session.exec(all_statement)
    all_resumes = list(all_result.all())
    for r in all_resumes:
        r.is_primary = False
        session.add(r)
    await session.flush()

    # Set target as primary
    target.is_primary = True
    session.add(target)
    await session.flush()

    log.info("resume_primary_set", user_id=user_id, resume_id=resume_id)
    return target


async def get_resume_download_url(resume: Resume) -> str:
    """Generate a presigned download URL for a resume file.

    Args:
        resume: The Resume model instance.

    Returns:
        A presigned URL string valid for the default expiry period.
    """
    url = await get_storage().generate_presigned_url(resume.storage_key)
    log.info(
        "resume_download_url_generated",
        resume_id=str(resume.id),
        storage_key=resume.storage_key,
    )
    return url
