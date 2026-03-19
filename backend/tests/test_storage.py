from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.services.storage import StorageService


class TestStorageService:
    """Unit tests for StorageService with mocked boto3 client."""

    def _make_service(self) -> StorageService:
        """Create a StorageService with a mocked boto3 client."""
        with patch("app.services.storage.boto3") as mock_boto3:
            mock_boto3.client.return_value = MagicMock()
            service = StorageService(
                account_id="test-account",
                access_key_id="test-key",
                secret_access_key="test-secret",
                bucket_name="test-bucket",
            )
        return service

    async def test_upload_file(self) -> None:
        service = self._make_service()
        result = await service.upload_file(
            "test/key.pdf", b"content", "application/pdf"
        )
        assert result == "test/key.pdf"
        service._client.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="test/key.pdf",
            Body=b"content",
            ContentType="application/pdf",
        )

    async def test_upload_file_returns_key(self) -> None:
        service = self._make_service()
        key = "resumes/user123/document.docx"
        result = await service.upload_file(key, b"docx-bytes", "application/docx")
        assert result == key

    async def test_delete_file(self) -> None:
        service = self._make_service()
        await service.delete_file("test/key.pdf")
        service._client.delete_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="test/key.pdf",
        )

    async def test_download_file(self) -> None:
        service = self._make_service()
        mock_body = MagicMock()
        mock_body.read.return_value = b"file-content"
        service._client.get_object.return_value = {"Body": mock_body}

        content = await service.download_file("test/key.pdf")
        assert content == b"file-content"
        service._client.get_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="test/key.pdf",
        )

    async def test_generate_presigned_url(self) -> None:
        service = self._make_service()
        service._client.generate_presigned_url.return_value = "https://signed-url"

        url = await service.generate_presigned_url("test/key.pdf")
        assert url == "https://signed-url"
        service._client.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={"Bucket": "test-bucket", "Key": "test/key.pdf"},
            ExpiresIn=3600,
        )

    async def test_generate_presigned_url_custom_expiry(self) -> None:
        service = self._make_service()
        service._client.generate_presigned_url.return_value = "https://signed-url"

        url = await service.generate_presigned_url("test/key.pdf", expires_in=7200)
        assert url == "https://signed-url"
        service._client.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={"Bucket": "test-bucket", "Key": "test/key.pdf"},
            ExpiresIn=7200,
        )
