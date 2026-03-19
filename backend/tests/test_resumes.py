from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _mock_storage() -> MagicMock:
    """Return a MagicMock that quacks like StorageService."""
    storage = MagicMock()
    storage.upload_file = AsyncMock(return_value="resumes/test/key.pdf")
    storage.delete_file = AsyncMock()
    storage.generate_presigned_url = AsyncMock(
        return_value="https://r2.example.com/signed-url"
    )
    return storage


# ---------------------------------------------------------------------------
# Upload tests
# ---------------------------------------------------------------------------


class TestUploadResume:
    """Tests for POST /api/v1/resumes."""

    @patch("app.services.resume.get_storage", return_value=_mock_storage())
    async def test_upload_pdf_success(
        self,
        mock_storage: MagicMock,
        client: AsyncClient,
        auth_headers: dict[str, str],
        sample_pdf_bytes: bytes,
    ) -> None:
        response = await client.post(
            "/api/v1/resumes",
            files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["resume"]["filename"] == "resume.pdf"
        assert data["resume"]["file_type"] == "pdf"
        assert data["resume"]["is_primary"] is True  # First resume is primary
        assert data["message"] == "Resume uploaded successfully"

    @patch("app.services.resume.get_storage", return_value=_mock_storage())
    async def test_upload_docx_success(
        self,
        mock_storage: MagicMock,
        client: AsyncClient,
        auth_headers: dict[str, str],
        sample_docx_bytes: bytes,
    ) -> None:
        response = await client.post(
            "/api/v1/resumes",
            files={
                "file": (
                    "resume.docx",
                    sample_docx_bytes,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["resume"]["filename"] == "resume.docx"
        assert data["resume"]["file_type"] == "docx"

    async def test_upload_invalid_type(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        response = await client.post(
            "/api/v1/resumes",
            files={"file": ("resume.txt", b"plain text", "text/plain")},
            headers=auth_headers,
        )
        assert response.status_code == 400

    async def test_upload_unauthenticated(
        self,
        client: AsyncClient,
        sample_pdf_bytes: bytes,
    ) -> None:
        response = await client.post(
            "/api/v1/resumes",
            files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
        )
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# List tests
# ---------------------------------------------------------------------------


class TestListResumes:
    """Tests for GET /api/v1/resumes."""

    async def test_list_empty(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        response = await client.get("/api/v1/resumes", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["resumes"] == []
        assert response.json()["total"] == 0

    @patch("app.services.resume.get_storage", return_value=_mock_storage())
    async def test_list_after_upload(
        self,
        mock_storage: MagicMock,
        client: AsyncClient,
        auth_headers: dict[str, str],
        sample_pdf_bytes: bytes,
    ) -> None:
        # Upload first
        await client.post(
            "/api/v1/resumes",
            files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
            headers=auth_headers,
        )
        # List
        response = await client.get("/api/v1/resumes", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["total"] == 1
        assert response.json()["resumes"][0]["filename"] == "resume.pdf"


# ---------------------------------------------------------------------------
# Get single resume tests
# ---------------------------------------------------------------------------


class TestGetResume:
    """Tests for GET /api/v1/resumes/{resume_id}."""

    @patch("app.services.resume.get_storage", return_value=_mock_storage())
    async def test_get_own_resume(
        self,
        mock_storage: MagicMock,
        client: AsyncClient,
        auth_headers: dict[str, str],
        sample_pdf_bytes: bytes,
    ) -> None:
        # Upload
        upload_resp = await client.post(
            "/api/v1/resumes",
            files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
            headers=auth_headers,
        )
        resume_id = upload_resp.json()["resume"]["id"]
        # Get
        response = await client.get(
            f"/api/v1/resumes/{resume_id}", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["filename"] == "resume.pdf"

    async def test_get_nonexistent(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        response = await client.get(
            f"/api/v1/resumes/{uuid.uuid4()}", headers=auth_headers
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Download URL tests
# ---------------------------------------------------------------------------


class TestDownloadResume:
    """Tests for GET /api/v1/resumes/{resume_id}/download."""

    @patch("app.services.resume.get_storage", return_value=_mock_storage())
    async def test_download_url(
        self,
        mock_storage: MagicMock,
        client: AsyncClient,
        auth_headers: dict[str, str],
        sample_pdf_bytes: bytes,
    ) -> None:
        # Upload
        upload_resp = await client.post(
            "/api/v1/resumes",
            files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
            headers=auth_headers,
        )
        resume_id = upload_resp.json()["resume"]["id"]
        # Download URL
        response = await client.get(
            f"/api/v1/resumes/{resume_id}/download", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["download_url"] == "https://r2.example.com/signed-url"
        assert data["filename"] == "resume.pdf"
        assert data["expires_in"] == 3600

    async def test_download_nonexistent(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        response = await client.get(
            f"/api/v1/resumes/{uuid.uuid4()}/download", headers=auth_headers
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Delete tests
# ---------------------------------------------------------------------------


class TestDeleteResume:
    """Tests for DELETE /api/v1/resumes/{resume_id}."""

    @patch("app.services.resume.get_storage", return_value=_mock_storage())
    async def test_delete_resume(
        self,
        mock_storage: MagicMock,
        client: AsyncClient,
        auth_headers: dict[str, str],
        sample_pdf_bytes: bytes,
    ) -> None:
        # Upload
        upload_resp = await client.post(
            "/api/v1/resumes",
            files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
            headers=auth_headers,
        )
        resume_id = upload_resp.json()["resume"]["id"]
        # Delete
        response = await client.delete(
            f"/api/v1/resumes/{resume_id}", headers=auth_headers
        )
        assert response.status_code == 204
        # Verify gone
        response2 = await client.get(
            f"/api/v1/resumes/{resume_id}", headers=auth_headers
        )
        assert response2.status_code == 404

    async def test_delete_nonexistent(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        response = await client.delete(
            f"/api/v1/resumes/{uuid.uuid4()}", headers=auth_headers
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Set primary tests
# ---------------------------------------------------------------------------


class TestSetPrimary:
    """Tests for PUT /api/v1/resumes/{resume_id}/primary."""

    @patch("app.services.resume.get_storage", return_value=_mock_storage())
    async def test_set_primary(
        self,
        mock_storage: MagicMock,
        client: AsyncClient,
        auth_headers: dict[str, str],
        sample_pdf_bytes: bytes,
    ) -> None:
        # Upload two resumes
        resp1 = await client.post(
            "/api/v1/resumes",
            files={"file": ("resume1.pdf", sample_pdf_bytes, "application/pdf")},
            headers=auth_headers,
        )
        resp2 = await client.post(
            "/api/v1/resumes",
            files={"file": ("resume2.pdf", sample_pdf_bytes, "application/pdf")},
            headers=auth_headers,
        )
        resume1_id = resp1.json()["resume"]["id"]
        resume2_id = resp2.json()["resume"]["id"]

        # First resume should be primary
        assert resp1.json()["resume"]["is_primary"] is True
        assert resp2.json()["resume"]["is_primary"] is False

        # Set second as primary
        response = await client.put(
            f"/api/v1/resumes/{resume2_id}/primary", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["is_primary"] is True

        # Verify first is no longer primary
        check_resp = await client.get(
            f"/api/v1/resumes/{resume1_id}", headers=auth_headers
        )
        assert check_resp.json()["is_primary"] is False

    async def test_set_primary_nonexistent(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        response = await client.put(
            f"/api/v1/resumes/{uuid.uuid4()}/primary", headers=auth_headers
        )
        assert response.status_code == 404
