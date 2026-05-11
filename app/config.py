"""Application configuration."""
import os
from datetime import timedelta

# Project root (parent of the `app` package)
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def default_sqlite_uri(filename: str = "iia_vbo.sqlite") -> str:
    """Absolute sqlite URI under project `instance/` (Flask also creates `instance/` at runtime)."""
    path = os.path.join(_PROJECT_ROOT, "instance", filename)
    # Four slashes after sqlite: for absolute path on POSIX (sqlite:////abs/path)
    return "sqlite:///" + path.replace(os.sep, "/")


class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "instance", "uploads"
    )
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(
        minutes=int(os.environ.get("SESSION_LIFETIME_MINUTES", "45"))
    )
    WTF_CSRF_TIME_LIMIT = None
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "localhost")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "25"))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "0") == "1"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get(
        "MAIL_DEFAULT_SENDER", "noreply@iia.res.in"
    )
    ORG_NAME = "Indian Institute of Astrophysics"
    ORG_UNIT = "Vainu Bappu Observatory, Kavalur"
    APP_TITLE = "IIA Vendor Bill & Inventory Management System"


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", default_sqlite_uri())


class ProductionConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", default_sqlite_uri())
    SESSION_COOKIE_SECURE = True


def get_config(name=None):
    env = name or os.environ.get("FLASK_ENV", "development")
    if env == "production":
        return ProductionConfig
    return DevelopmentConfig
