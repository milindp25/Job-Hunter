from __future__ import annotations

import asyncio

import boto3
import structlog
from botocore.config import Config as BotoConfig

from app.config import get_settings

log = structlog.get_logger()


class StorageService:
    """S3-compatible object storage client for Cloudflare R2."""

    def __init__(
        self,
        account_id: str,
        access_key_id: str,
        secret_access_key: str,
        bucket_name: str,
    ) -> None:
        self._bucket_name = bucket_name
        self._client = boto3.client(
            "s3",
            endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            config=BotoConfig(
                region_name="auto",
                signature_version="s3v4",
            ),
        )
        log.info("storage_service_initialized", bucket=bucket_name)

    async def upload_file(
        self,
        key: str,
        content: bytes,
        content_type: str,
    ) -> str:
        """Upload bytes to R2. Returns the storage key."""
        await asyncio.to_thread(
            self._client.put_object,
            Bucket=self._bucket_name,
            Key=key,
            Body=content,
            ContentType=content_type,
        )
        log.info("file_uploaded", key=key, size=len(content))
        return key

    async def download_file(self, key: str) -> bytes:
        """Download file content from R2."""
        response = await asyncio.to_thread(
            self._client.get_object,
            Bucket=self._bucket_name,
            Key=key,
        )
        content: bytes = response["Body"].read()
        log.info("file_downloaded", key=key, size=len(content))
        return content

    async def delete_file(self, key: str) -> None:
        """Delete an object from R2."""
        await asyncio.to_thread(
            self._client.delete_object,
            Bucket=self._bucket_name,
            Key=key,
        )
        log.info("file_deleted", key=key)

    async def generate_presigned_url(
        self,
        key: str,
        expires_in: int = 3600,
    ) -> str:
        """Generate a presigned URL for direct download."""
        url: str = await asyncio.to_thread(
            self._client.generate_presigned_url,
            "get_object",
            Params={"Bucket": self._bucket_name, "Key": key},
            ExpiresIn=expires_in,
        )
        log.info("presigned_url_generated", key=key, expires_in=expires_in)
        return url


# Module-level singleton (lazy initialized)
_storage: StorageService | None = None


def get_storage() -> StorageService:
    """Return the storage service singleton, creating it if needed."""
    global _storage  # noqa: PLW0603
    if _storage is None:
        settings = get_settings()
        if not settings.R2_ACCOUNT_ID or not settings.R2_ACCESS_KEY_ID:
            raise RuntimeError(
                "R2 storage is not configured. "
                "Set R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY in .env"
            )
        _storage = StorageService(
            account_id=settings.R2_ACCOUNT_ID,
            access_key_id=settings.R2_ACCESS_KEY_ID,
            secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            bucket_name=settings.R2_BUCKET_NAME,
        )
    return _storage
