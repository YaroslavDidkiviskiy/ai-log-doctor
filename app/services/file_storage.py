import uuid
from pathlib import Path

from fastapi import UploadFile

from app.config import settings


def validate_extension(filename: str) -> bool:
    ext = Path(filename).suffix.lower()
    return ext in settings.ALLOWED_EXTENSIONS


async def save_upload(file: UploadFile) -> tuple[str, str]:
    """Save uploaded file to disk. Returns (stored_filename, stored_path)."""
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename or "upload.log").suffix.lower()
    stored_name = f"{uuid.uuid4().hex}{ext}"
    stored_path = settings.UPLOAD_DIR / stored_name

    content = await file.read()
    if len(content) > settings.max_upload_bytes:
        raise ValueError(
            f"File exceeds maximum size of {settings.MAX_UPLOAD_SIZE_MB} MB"
        )

    stored_path.write_bytes(content)
    return stored_name, str(stored_path)
