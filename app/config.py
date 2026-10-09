import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "lostfound-dev-fallback-key-2026")
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/lostfound_db")
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "app" / "static" / "uploads"))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 5 * 1024 * 1024))  # 5MB
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False  # Set True in production with HTTPS
    
    # Defaults
    RETENTION_DAYS_DEFAULT = int(os.getenv("RETENTION_DAYS_DEFAULT", 30))
    STRONG_MATCH_THRESHOLD_DEFAULT = int(os.getenv("STRONG_MATCH_THRESHOLD_DEFAULT", 60))
    DUPLICATE_WINDOW_DAYS_DEFAULT = int(os.getenv("DUPLICATE_WINDOW_DAYS_DEFAULT", 2))
    ITEMS_PER_PAGE = 10


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    MONGO_URI = "mongodb://127.0.0.1:27017/lostfound_test_db"
