"""Single place where evidence frames get written to disk.

Evidence frames are stored as JPEG **files** (``Pothole.frame_image``); the
database holds only the relative path. The old ``frame_image_base64``
TextField is gone -- see Plan/EVIDENCE_STORAGE.md for the reasoning.

Two entry points:

``save_frame_bytes``
    The normal path. The mobile app POSTs raw JPEG bytes as
    ``multipart/form-data`` and they land here untouched.

``save_frame_base64``
    Compatibility shim for the legacy CSV importers, whose source data has
    base64 blobs embedded in a ``Frame_Data`` column. Decodes once at import
    time so nothing base64-shaped is ever persisted.
"""
from __future__ import annotations

import base64
import binascii
import logging

from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)

# Frames are evidence thumbnails, not archival photos. Anything past a couple
# of MB means the caller sent a full-resolution still by mistake.
MAX_FRAME_BYTES = 4 * 1024 * 1024

JPEG_MAGIC = b"\xff\xd8\xff"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


class FrameStorageError(ValueError):
    """Raised when the supplied frame data is unusable."""


def _filename(pothole_id: int | str | None, frame_number: int | None) -> str:
    pid = pothole_id if pothole_id is not None else "new"
    fnum = frame_number if frame_number is not None else "x"
    return f"pothole_{pid}_frame_{fnum}.jpg"


def looks_like_image(data: bytes) -> bool:
    return data.startswith(JPEG_MAGIC) or data.startswith(PNG_MAGIC)


def save_frame_bytes(
    pothole,
    data: bytes,
    frame_number: int | None = None,
    *,
    save: bool = True,
) -> str:
    """Attach raw image bytes to ``pothole.frame_image``.

    Returns the stored relative path. Raises FrameStorageError on bad input.
    """
    if not data:
        raise FrameStorageError("Empty frame data")
    if len(data) > MAX_FRAME_BYTES:
        raise FrameStorageError(
            f"Frame is {len(data)} bytes, over the {MAX_FRAME_BYTES}-byte limit"
        )
    if not looks_like_image(data):
        raise FrameStorageError("Frame data is not a JPEG or PNG image")

    name = _filename(getattr(pothole, "pk", None), frame_number)
    pothole.frame_image.save(name, ContentFile(data, name=name), save=save)
    return pothole.frame_image.name


def save_frame_base64(
    pothole,
    b64: str | None,
    frame_number: int | None = None,
    *,
    save: bool = True,
) -> str | None:
    """Decode a legacy base64 blob and store it as a file.

    Tolerates ``data:image/jpeg;base64,...`` data-URI prefixes. Returns None
    (rather than raising) when the blob is missing or undecodable, so a single
    bad row cannot abort a long CSV import.
    """
    if not b64:
        return None

    payload = b64.strip()
    if "base64," in payload:
        payload = payload.split("base64,", 1)[1]

    try:
        data = base64.b64decode(payload, validate=False)
    except (binascii.Error, ValueError) as exc:
        logger.warning("Skipping undecodable base64 frame: %s", exc)
        return None

    try:
        return save_frame_bytes(pothole, data, frame_number, save=save)
    except FrameStorageError as exc:
        logger.warning("Skipping unusable base64 frame: %s", exc)
        return None
