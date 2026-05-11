"""Application factory."""
import importlib
import os

from flask import Flask

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    def load_dotenv(*args, **kwargs):
        return False

from app.config import get_config
from app.extensions import csrf, db, login_manager, migrate


def create_app(config_name=None):
    load_dotenv()
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
        instance_relative_config=True,
    )
    cfg = get_config(config_name)
    app.config.from_object(cfg)

    db_uri = str(app.config.get("SQLALCHEMY_DATABASE_URI") or "")
    if db_uri.startswith("sqlite"):
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "connect_args": {"check_same_thread": False},
        }
    else:
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_pre_ping": True,
            "pool_recycle": 280,
        }

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    importlib.import_module("app.models")  # register all tables; avoid "import app.models" (shadows Flask `app`)

    from app.db_bootstrap import init_database

    init_database(app)

    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    register_blueprints(app)

    from app.cli import register_cli

    register_cli(app)

    @app.context_processor
    def inject_config():
        return {
            "ORG_NAME": app.config.get("ORG_NAME"),
            "ORG_UNIT": app.config.get("ORG_UNIT"),
            "APP_TITLE": app.config.get("APP_TITLE"),
        }

    return app


def register_blueprints(app):
    from app.blueprints.auth import bp as auth_bp
    from app.blueprints.main import bp as main_bp
    from app.blueprints.about import bp as about_bp
    from app.blueprints.vendors import bp as vendors_bp
    from app.blueprints.bills import bp as bills_bp
    from app.blueprints.inventory import bp as inventory_bp
    from app.blueprints.employees import bp as employees_bp
    from app.blueprints.issues import bp as issues_bp
    from app.blueprints.reports import bp as reports_bp
    from app.blueprints.admin import bp as admin_bp
    from app.blueprints.api import bp as api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(about_bp)
    app.register_blueprint(vendors_bp, url_prefix="/vendors")
    app.register_blueprint(bills_bp, url_prefix="/bills")
    app.register_blueprint(inventory_bp, url_prefix="/inventory")
    app.register_blueprint(employees_bp, url_prefix="/employees")
    app.register_blueprint(issues_bp, url_prefix="/issues")
    app.register_blueprint(reports_bp, url_prefix="/reports")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(api_bp, url_prefix="/api")
