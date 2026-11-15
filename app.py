import os
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, render_template, jsonify
from flask_login import LoginManager
from flask_cors import CORS

from config import Config
from database import db
from database.models import User, VerificationReport
from utils.helpers import get_verdict_meta, get_confidence_tier, time_ago


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please sign in to access your saved reports and dashboard."
    login_manager.login_message_category = "info"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Jinja context processors & filters
    @app.context_processor
    def inject_globals():
        return {
            "current_year": datetime.now(timezone.utc).year,
            "get_verdict_meta": get_verdict_meta,
            "get_confidence_tier": get_confidence_tier,
            "time_ago": time_ago,
        }

    @app.template_filter("timeago")
    def timeago_filter(dt):
        return time_ago(dt)

    # Register Blueprints
    from routes import views_bp, auth_bp, api_bp
    app.register_blueprint(views_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)

    # Ensure required upload directories exist
    upload_base = Path(app.config["UPLOAD_FOLDER"])
    for subdir in ["images", "videos", "ela", "videos/frames"]:
        (upload_base / subdir).mkdir(parents=True, exist_ok=True)

    # Database initialization & sample seed data creation
    with app.app_context():
        # Ensure database directory exists
        db_path = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        if "sqlite:///" in db_path:
            db_file = db_path.replace("sqlite:///", "")
            if db_file != ":memory:":
                Path(db_file).parent.mkdir(parents=True, exist_ok=True)
        db.create_all()

    # Friendly, secure error handlers
    @app.errorhandler(400)
    def bad_request(e):
        if app.config.get("TESTING") or "/api/" in (getattr(e, "description", "") or ""):
            return jsonify({"success": False, "error": "Bad request"}), 400
        return render_template("errors/400.html"), 400

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def request_entity_too_large(e):
        return jsonify({"success": False, "error": "File exceeds the allowed size limit (10MB for images, 50MB for video)."}), 413

    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({"success": False, "error": "Too many requests. Please throttle your verification checks."}), 429

    @app.errorhandler(500)
    def internal_error(e):
        return render_template("errors/500.html"), 500

    return app


app = create_app()

if __name__ == "__main__":
    # College-level demonstration startup
    print("\n" + "=" * 60)
    print("   TRUTH AI — AI-Powered Fake News & Media Detection Engine")
    print("   Verify. Analyze. Trust.")
    print("=" * 60)
    print("   Server running on: http://127.0.0.1:5000")
    print("   Press CTRL+C to terminate the development server.\n")
    app.run(host="127.0.0.1", port=5000, debug=True)
