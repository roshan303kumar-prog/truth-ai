import os
import re
import time
from collections import defaultdict
from werkzeug.utils import secure_filename

# Magic bytes definitions for reliable file type sniffing
IMAGE_SIGNATURES = {
    "jpeg": [b"\xff\xd8\xff"],
    "jpg": [b"\xff\xd8\xff"],
    "png": [b"\x89PNG\r\n\x1a\n"],
    "webp": [b"RIFF"],  # WebP also has WEBP at offset 8
}

VIDEO_SIGNATURES = {
    "mp4": [b"ftyp", b"\x00\x00\x00\x18ftyp", b"\x00\x00\x00\x1cftyp", b"\x00\x00\x00\x20ftyp"],
    "webm": [b"\x1a\x45\xdf\xa3"],  # EBML header
    "avi": [b"RIFF"],               # RIFF....AVI
    "mov": [b"moov", b"mdat", b"wide", b"free", b"skip", b"ftypqt  "],
}


def sanitize_input_text(text: str, max_length: int = 10000) -> str:
    """Sanitize and clamp user text inputs to prevent memory or injection attacks."""
    if not text:
        return ""
    text = str(text).strip()
    # Remove null bytes and non-printable control characters (except newline, carriage return, tab)
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)
    if len(text) > max_length:
        text = text[:max_length]
    return text


def validate_image_file(file_storage, max_size_bytes: int = 10 * 1024 * 1024) -> tuple[bool, str, str]:
    """
    Validates uploaded image file:
    1. Checks filename and extension
    2. Checks file size
    3. Inspects real file magic bytes (preventing file extension spoofing)
    Returns: (is_valid, safe_extension, error_message)
    """
    if not file_storage or not file_storage.filename:
        return False, "", "No file selected."

    filename = secure_filename(file_storage.filename)
    if not filename or "." not in filename:
        return False, "", "Invalid filename."

    ext = filename.rsplit(".", 1)[1].lower()
    if ext not in ["jpg", "jpeg", "png", "webp"]:
        return False, "", f"Unsupported image format: .{ext}. Allowed: JPG, JPEG, PNG, WEBP."

    # Check size by seeking
    file_storage.seek(0, os.SEEK_END)
    size = file_storage.tell()
    file_storage.seek(0)

    if size == 0:
        return False, "", "The uploaded file is empty."
    if size > max_size_bytes:
        return False, "", f"File size exceeds the {max_size_bytes // (1024 * 1024)}MB limit."

    # Read leading bytes for magic signature inspection
    header = file_storage.read(32)
    file_storage.seek(0)

    if ext in ["jpg", "jpeg"]:
        if not header.startswith(b"\xff\xd8\xff"):
            return False, "", "File header does not match a valid JPEG image."
    elif ext == "png":
        if not header.startswith(b"\x89PNG\r\n\x1a\n"):
            return False, "", "File header does not match a valid PNG image."
    elif ext == "webp":
        if not (header.startswith(b"RIFF") and b"WEBP" in header[:16]):
            return False, "", "File header does not match a valid WEBP image."

    return True, ext, ""


def validate_video_file(file_storage, max_size_bytes: int = 50 * 1024 * 1024) -> tuple[bool, str, str]:
    """
    Validates uploaded video file:
    1. Filename & extension
    2. Size limits
    3. Magic signature verification
    Returns: (is_valid, safe_extension, error_message)
    """
    if not file_storage or not file_storage.filename:
        return False, "", "No video file selected."

    filename = secure_filename(file_storage.filename)
    if not filename or "." not in filename:
        return False, "", "Invalid video filename."

    ext = filename.rsplit(".", 1)[1].lower()
    if ext not in ["mp4", "webm", "avi", "mov"]:
        return False, "", f"Unsupported video format: .{ext}. Allowed: MP4, WEBM, AVI, MOV."

    file_storage.seek(0, os.SEEK_END)
    size = file_storage.tell()
    file_storage.seek(0)

    if size == 0:
        return False, "", "The uploaded video is empty."
    if size > max_size_bytes:
        return False, "", f"Video exceeds the {max_size_bytes // (1024 * 1024)}MB limit."

    header = file_storage.read(64)
    file_storage.seek(0)

    # Magic byte verification
    if ext == "mp4":
        if b"ftyp" not in header[:32]:
            return False, "", "File header does not match standard MP4 container specifications."
    elif ext == "webm":
        if not header.startswith(b"\x1a\x45\xdf\xa3"):
            return False, "", "File header does not match standard WEBM/EBML container."
    elif ext == "avi":
        if not (header.startswith(b"RIFF") and b"AVI " in header[:16]):
            return False, "", "File header does not match standard AVI container."
    elif ext == "mov":
        if not any(sig in header[:32] for sig in [b"moov", b"mdat", b"wide", b"free", b"ftypqt"]):
            return False, "", "File header does not match QuickTime/MOV container."

    return True, ext, ""


class SimpleRateLimiter:
    """In-memory sliding-window rate limiter per client IP."""
    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)

    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds
        # Clean older requests
        self.requests[client_ip] = [ts for ts in self.requests[client_ip] if ts > window_start]
        if len(self.requests[client_ip]) >= self.max_requests:
            return False
        self.requests[client_ip].append(now)
        return True


# Global rate limiter instance: 40 requests per 60 seconds per IP
rate_limiter = SimpleRateLimiter(max_requests=40, window_seconds=60)
