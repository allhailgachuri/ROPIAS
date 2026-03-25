"""
app.py — Application factory for ROPIAS.

Database selection:
  Development:  DATABASE_URL=sqlite:///database/ropias.db
  Production:   DATABASE_URL=postgresql://user:pass@host:5432/ropias

The app auto-detects which to use from the environment variable.
SQLite is never used in production (Railway/Render provide PostgreSQL).
"""

import sys
import os

# Add src to path safely relative to the file location
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, redirect, url_for
from flask_login import LoginManager, current_user
from flask_cors import CORS
from dotenv import load_dotenv
from database.models import db, User
from database.seed import seed_users

load_dotenv()


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    CORS(app)

    # ── Configuration ─────────────────────────────────────────────────────────
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-key-change-in-production")

    # Auto-select database
    database_url = os.getenv("DATABASE_URL", "sqlite:///database/ropias.db")
    
    # If using local SQLite, ensure the persistent hidden home database path is used on Windows
    # Workaround for SQLite C-library path encoding bug with emojis on Windows
    if "sqlite:///" in database_url and not ("memory" in database_url):
        safe_db_dir = os.path.expanduser('~/.ropias/database')
        os.makedirs(safe_db_dir, exist_ok=True)
        db_path = os.path.join(safe_db_dir, 'ropias.db').replace('\\', '/')
        database_url = f"sqlite:///{db_path}"

    # Railway/Render use postgres:// but SQLAlchemy needs postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # ── Extensions ────────────────────────────────────────────────────────────
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access ROPIAS."
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ── Blueprints ────────────────────────────────────────────────────────────
    from auth.routes import auth_bp
    from app.routes.farmer_routes import farmer_bp
    from app.routes.officer_routes import officer_bp
    from app.routes.api_routes import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(farmer_bp)
    app.register_blueprint(officer_bp)
    app.register_blueprint(api_bp)

    # ── Jinja globals ─────────────────────────────────────────────────────────
    from datetime import datetime
    @app.context_processor
    def inject_globals():
        return {"now": datetime.utcnow()}

    # ── Root redirect ─────────────────────────────────────────────────────────
    @app.route("/")
    def index():
        """Root: redirect to login if not authenticated, else to role dashboard."""
        if current_user.is_authenticated:
            if current_user.is_admin:
                return redirect(url_for("officer.dashboard"))
            return redirect(url_for("farmer.dashboard"))
        return redirect(url_for("auth.login"))

    # ── Database init + seed ──────────────────────────────────────────────────
    with app.app_context():
        db.create_all()
        # Seed the 3 foundational users only if they don't exist
        seed_users(db, User)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)