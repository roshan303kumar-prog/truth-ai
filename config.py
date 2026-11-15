import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

db_env = os.environ.get("DATABASE_URL", "").strip()
if db_env and not db_env.startswith("sqlite:///:memory:"):
    # Render and Heroku use 'postgres://' which SQLAlchemy 1.4+ rejects; rewrite to 'postgresql://'
    if db_env.startswith("postgres://"):
        DB_URI = db_env.replace("postgres://", "postgresql://", 1)
    elif db_env.startswith("sqlite:///"):
        clean_path = db_env.replace("sqlite:///", "")
        if not Path(clean_path).is_absolute():
            resolved_db = (BASE_DIR / clean_path).resolve()
        else:
            resolved_db = Path(clean_path).resolve()
        DB_URI = f"sqlite:///{resolved_db.as_posix()}"
    else:
        DB_URI = db_env
else:
    default_db = (BASE_DIR / "database" / "truth_ai.db").resolve()
    DB_URI = f"sqlite:///{default_db.as_posix()}"


class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "truth-ai-secure-dev-session-key-2026-xyz789")
    SQLALCHEMY_DATABASE_URI = DB_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Uploads
    UPLOAD_FOLDER = BASE_DIR / "uploads"
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB max request size
    MAX_IMAGE_SIZE = 10 * 1024 * 1024     # 10 MB image size limit
    MAX_VIDEO_SIZE = 50 * 1024 * 1024     # 50 MB video size limit

    ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
    ALLOWED_VIDEO_EXTENSIONS = {"mp4", "avi", "mov", "webm"}

    # External APIs (Optional - system falls back gracefully to DuckDuckGo/Wikipedia/Forensics)
    GOOGLE_FACT_CHECK_API_KEY = os.environ.get("GOOGLE_FACT_CHECK_API_KEY", "").strip()
    NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "").strip()
    DUCKDUCKGO_ENABLED = os.environ.get("DUCKDUCKGO_ENABLED", "True").lower() in ("true", "1", "yes")
    WIKIPEDIA_ENABLED = os.environ.get("WIKIPEDIA_ENABLED", "True").lower() in ("true", "1", "yes")
    OFFLINE_FALLBACK_ENABLED = os.environ.get("OFFLINE_FALLBACK_ENABLED", "True").lower() in ("true", "1", "yes")

    # AI Chat & Screen-Aware Vision Assistant (Supports Gemini, OpenAI, or smart local multimodal fallback)
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", os.environ.get("GOOGLE_API_KEY", "")).strip()
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
    ASSISTANT_MODEL = os.environ.get("ASSISTANT_MODEL", "gemini-1.5-flash").strip()

    # Forensic Analysis Parameters
    ELA_QUALITY = int(os.environ.get("ELA_QUALITY", 90))
    ELA_SCALE = int(os.environ.get("ELA_SCALE", 15))
    MAX_VIDEO_FRAMES = int(os.environ.get("MAX_VIDEO_FRAMES", 12))

    # Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"


class TestConfig(Config):
    """Testing configuration with in-memory database."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    OFFLINE_FALLBACK_ENABLED = True
