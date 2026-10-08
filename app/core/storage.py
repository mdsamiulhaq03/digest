"""Uploaded files on disk. Callers deal in storage keys; only this module knows
they map to paths under UPLOAD_DIR."""

from pathlib import Path
from typing import BinaryIO

from app.core.config import get_settings
from app.core.exceptions import FileTooLargeError

CHUNK_SIZE = 1024 * 1024


def path_for(storage_key: str) -> Path:
    return Path(get_settings().upload_dir) / storage_key


def save(source: BinaryIO, storage_key: str) -> int:
    """Copy source to disk a chunk at a time and return its size in bytes.

    Written to a .part file and renamed only once complete, so a reader never
    sees half a file. Over the size limit, the partial file is removed and
    FileTooLargeError is raised - the whole upload is never held in memory."""
    max_bytes = get_settings().max_upload_bytes
    final_path = path_for(storage_key)
    partial_path = final_path.with_name(f"{final_path.name}.part")
    size = 0
    try:
        with partial_path.open("wb") as destination:
            while chunk := source.read(CHUNK_SIZE):
                size += len(chunk)
                if size > max_bytes:
                    raise FileTooLargeError(max_bytes)
                destination.write(chunk)
        partial_path.replace(final_path)
    finally:
        partial_path.unlink(missing_ok=True)
    return size


def delete(storage_key: str) -> None:
    path_for(storage_key).unlink(missing_ok=True)
