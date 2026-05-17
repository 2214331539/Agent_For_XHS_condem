from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import get_settings


class StorageService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def save_upload(self, file: UploadFile, folder: str) -> dict[str, str | int | None]:
        if self.settings.storage_backend == "aliyun_oss":
            return await self._save_aliyun_oss(file, folder)
        return await self._save_local(file, folder)

    async def _save_local(self, file: UploadFile, folder: str) -> dict[str, str | int | None]:
        suffix = Path(file.filename or "").suffix or ".bin"
        object_key = f"{folder.strip('/')}/{uuid4()}{suffix}"
        target = Path(self.settings.local_storage_dir) / object_key
        target.parent.mkdir(parents=True, exist_ok=True)

        content = await file.read()
        target.write_bytes(content)

        base_url = self.settings.public_media_base_url.rstrip("/")
        return {
            "object_key": object_key,
            "image_url": f"{base_url}/{object_key}",
            "file_size": len(content),
            "mime_type": file.content_type,
        }

    async def _save_aliyun_oss(self, file: UploadFile, folder: str) -> dict[str, str | int | None]:
        raise NotImplementedError("aliyun_oss storage is configured but the OSS client is not installed yet.")


storage_service = StorageService()

