import io
from werkzeug.datastructures import FileStorage
from utils.security import (
    sanitize_input_text,
    validate_image_file,
    validate_video_file,
    SimpleRateLimiter,
)


def test_sanitize_input_text():
    dirty = "Hello\x00World\x08! <script>alert(1)</script>"
    clean = sanitize_input_text(dirty)
    assert "\x00" not in clean
    assert "\x08" not in clean
    assert "Hello" in clean


def test_validate_image_magic_bytes_spoofing():
    # A fake file with .jpg extension but containing plain text instead of JPEG header
    buf = io.BytesIO(b"This is just plain text, not a real JPEG image.")
    fs = FileStorage(stream=buf, filename="malicious.jpg", content_type="image/jpeg")

    is_valid, ext, err = validate_image_file(fs)
    assert is_valid is False
    assert "File header does not match" in err


def test_validate_image_valid_jpeg():
    # Real JPEG starting with \xff\xd8\xff
    buf = io.BytesIO(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00" + b"\x00" * 20)
    fs = FileStorage(stream=buf, filename="authentic.jpg", content_type="image/jpeg")

    is_valid, ext, err = validate_image_file(fs)
    assert is_valid is True
    assert ext == "jpg"
    assert err == ""


def test_rate_limiter():
    limiter = SimpleRateLimiter(max_requests=3, window_seconds=10)
    ip = "192.168.1.50"

    assert limiter.is_allowed(ip) is True
    assert limiter.is_allowed(ip) is True
    assert limiter.is_allowed(ip) is True
    # 4th request within window must be blocked
    assert limiter.is_allowed(ip) is False
