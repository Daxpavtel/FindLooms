import os
from datetime import datetime
from flask import Flask, render_template
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from apscheduler.schedulers.background import BackgroundScheduler

from app.config import Config
from app.db import init_db, close_db
from app.auth_utils import load_user_from_db
from app.services.archive import run_archive_check

login_manager = LoginManager()
csrf = CSRFProtect()
scheduler = BackgroundScheduler()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please sign in to access this page."
    login_manager.login_message_category = "info"
    login_manager.user_loader(load_user_from_db)

    csrf.init_app(app)

    # Teardown DB connection on request end
    app.teardown_appcontext(close_db)

    # Initialize collections and indexes idempotently
    try:
        init_db(app.config["MONGO_URI"])
    except Exception as e:
        app.logger.warning(f"Database init warning (may run in test mode): {e}")

    # Register Blueprints
    from app.blueprints.auth import auth_bp
    from app.blueprints.lost import lost_bp
    from app.blueprints.found import found_bp
    from app.blueprints.claims import claims_bp
    from app.blueprints.kanban import kanban_bp
    from app.blueprints.views import views_bp
    from app.blueprints.reports import reports_bp
    from app.blueprints.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(lost_bp)
    app.register_blueprint(found_bp)
    app.register_blueprint(claims_bp)
    app.register_blueprint(kanban_bp)
    app.register_blueprint(views_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(admin_bp)

    # Landing page
    @app.route("/")
    def index():
        from app.db import get_db
        db = get_db()
        stats = {
            "total_lost": db.lost_items.count_documents({}),
            "total_found": db.found_items.count_documents({}),
            "total_returned": db.found_items.count_documents({"status": "Returned"})
        }
        return render_template("index.html", stats=stats)

    # Custom Error Handlers (403, 404, 500)
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template("403.html"), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template("500.html"), 500

    # Jinja Helpers and Filters
    @app.template_filter("timeago")
    def timeago_filter(dt):
        if not dt or not isinstance(dt, datetime):
            return ""
        diff = datetime.utcnow() - dt
        if diff.days > 0:
            return f"{diff.days}d ago"
        hrs = diff.seconds // 3600
        if hrs > 0:
            return f"{hrs}h ago"
        mins = diff.seconds // 60
        return f"{max(1, mins)}m ago"

    @app.template_filter("format_date")
    def format_date(dt, fmt="%b %d, %Y"):
        if not dt:
            return ""
        if isinstance(dt, datetime):
            return dt.strftime(fmt)
        return str(dt)

    # Initialize APScheduler for daily archive job (if not running in test mode)
    if not app.config.get("TESTING") and not os.environ.get("WERKZEUG_RUN_MAIN") == "false":
        if not scheduler.running:
            # Run once daily at 02:00 AM
            scheduler.add_job(
                func=lambda: _run_scheduled_archive(app),
                trigger="cron",
                hour=2,
                minute=0,
                id="daily_archive_check",
                replace_existing=True
            )
            scheduler.start()

    return app


def _run_scheduled_archive(app):
    """Context wrapper for background archive job."""
    with app.app_context():
        try:
            run_archive_check()
        except Exception as e:
            app.logger.error(f"Scheduled archive check failed: {e}")
