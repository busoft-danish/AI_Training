from pathlib import Path

import boto3
import structlog
from botocore.exceptions import BotoCoreError, ClientError

from utils.exceptions import UploadError

log = structlog.get_logger(__name__)


class UploadService:
    """Uploads markdown files to MinIO (S3-compatible storage).

    boto3 is synchronous; we keep it in a service so it can be swapped
    for an async client later without touching the rest of the pipeline.
    """

    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket: str) -> None:
        self._bucket = bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        """Create the bucket if it doesn't exist yet."""
        try:
            self._client.head_bucket(Bucket=self._bucket)
        except ClientError:
            self._client.create_bucket(Bucket=self._bucket)
            log.info("minio.bucket_created", bucket=self._bucket)

    def upload(self, local_path: Path, s3_key: str) -> None:
        """Upload a local file to MinIO under the given S3 key."""
        try:
            self._client.upload_file(
                str(local_path),
                self._bucket,
                s3_key,
                ExtraArgs={"ContentType": "text/markdown"},
            )
            log.info("minio.uploaded", s3_key=s3_key)
        except (BotoCoreError, ClientError) as exc:
            raise UploadError(f"Upload failed for {s3_key}: {exc}") from exc

    def delete(self, s3_key: str) -> None:
        """Delete an object from MinIO."""
        try:
            self._client.delete_object(Bucket=self._bucket, Key=s3_key)
            log.info("minio.deleted", s3_key=s3_key)
        except (BotoCoreError, ClientError) as exc:
            raise UploadError(f"Delete failed for {s3_key}: {exc}") from exc
