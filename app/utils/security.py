"""Secure tokens and upload helpers."""
import secrets
from hashlib import sha256
from pathlib import Path

from werkzeug.utils import secure_filename


def hash_token(raw_token: str) -> str:
    return sha256(raw_token.encode("utf-8")).hexdigest()


def generate_token() -> str:
    return secrets.token_urlsafe(32)


def allowed_file(filename: str, allowed_extensions: set) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in allowed_extensions
    )


def save_upload(file_storage, upload_folder: str, prefix: str = "") -> str:
    """Return relative path stored in DB."""
    name = secure_filename(file_storage.filename or "file")
    stem = Path(name).stem[:80] or "file"
    ext = Path(name).suffix.lower()
    rel = f"{prefix}{secrets.token_hex(8)}_{stem}{ext}"
    dest = Path(upload_folder) / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    file_storage.save(dest)
    return rel
