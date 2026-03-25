"""
models.py
==========
SQLAlchemy ORM models for ROPIAS.
Supports both SQLite (development) and PostgreSQL (production).
The DATABASE_URL environment variable controls which is used.
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """
    Represents both admin (extension officer) and farmer users.
    Role field: 'admin' or 'farmer'.
    Seeded users cannot be deleted.
    """
    __tablename__ = "users"

    id               = db.Column(db.Integer, primary_key=True)
    full_name        = db.Column(db.String(120), nullable=False)
    username         = db.Column(db.String(80), unique=True, nullable=False)
    email            = db.Column(db.String(180), unique=True, nullable=False)
    password_hash    = db.Column(db.String(256), nullable=True) # Nullable for Google OAuth users
    google_id        = db.Column(db.String(100), unique=True, nullable=True)
    role             = db.Column(db.String(20), nullable=False, default="farmer")
    phone            = db.Column(db.String(30), nullable=True)
    is_active        = db.Column(db.Boolean, default=True, nullable=False)
    is_seeded        = db.Column(db.Boolean, default=False, nullable=False)
    greeting         = db.Column(db.Text, nullable=True)
    avatar_initials  = db.Column(db.String(3), nullable=True)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)
    last_login       = db.Column(db.DateTime, nullable=True)

    # Farmer-specific fields
    farm_latitude    = db.Column(db.Float, nullable=True)
    farm_longitude   = db.Column(db.Float, nullable=True)
    preferred_crop   = db.Column(db.String(50), nullable=True, default="maize")
    whatsapp_alerts  = db.Column(db.Boolean, default=True)
    sms_alerts       = db.Column(db.Boolean, default=False)

    # Relationships
    queries          = db.relationship("QueryLog", backref="user", lazy=True)
    alert_logs       = db.relationship("AlertLog", backref="user", lazy=True)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_farmer(self) -> bool:
        return self.role == "farmer"

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


class QueryLog(db.Model):
    """
    Stores every analysis request made through the system.
    Used for history, impact metrics, and ML training data.
    """
    __tablename__ = "query_logs"

    id               = db.Column(db.Integer, primary_key=True)
    user_id          = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)
    latitude         = db.Column(db.Float, nullable=False)
    longitude        = db.Column(db.Float, nullable=False)
    crop_key         = db.Column(db.String(50), nullable=True)
    onset_result     = db.Column(db.String(50), nullable=True)
    onset_color      = db.Column(db.String(20), nullable=True)
    moisture_pct     = db.Column(db.Float, nullable=True)
    irrigation_status= db.Column(db.String(80), nullable=True)
    data_start       = db.Column(db.String(20), nullable=True)
    data_end         = db.Column(db.String(20), nullable=True)
    session_id       = db.Column(db.String(64), nullable=True)


class AlertLog(db.Model):
    """
    Records every WhatsApp and SMS alert sent through the system.
    Tracks delivery status and farmer responses.
    """
    __tablename__ = "alert_logs"

    id               = db.Column(db.Integer, primary_key=True)
    user_id          = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    sent_at          = db.Column(db.DateTime, default=datetime.utcnow)
    channel          = db.Column(db.String(20), nullable=False)  # 'whatsapp' or 'sms'
    message_sid      = db.Column(db.String(60), nullable=True)   # Twilio message SID
    message_type     = db.Column(db.String(30), nullable=True)   # 'onset', 'irrigation', 'welcome'
    content_summary  = db.Column(db.Text, nullable=True)
    delivery_status  = db.Column(db.String(30), nullable=True)   # 'sent', 'delivered', 'failed'
    farmer_reply     = db.Column(db.Text, nullable=True)
    reply_at         = db.Column(db.DateTime, nullable=True)


class FarmFeedback(db.Model):
    """
    Stores ground-truth feedback from farmers (e.g. 'NO RAIN today').
    Used to validate and improve ML model predictions over time.
    """
    __tablename__ = "farm_feedback"

    id               = db.Column(db.Integer, primary_key=True)
    user_id          = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    submitted_at     = db.Column(db.DateTime, default=datetime.utcnow)
    latitude         = db.Column(db.Float, nullable=True)
    longitude        = db.Column(db.Float, nullable=True)
    feedback_type    = db.Column(db.String(30), nullable=False)  # 'no_rain', 'planted', 'crop_failed'
    notes            = db.Column(db.Text, nullable=True)
    system_prediction= db.Column(db.String(50), nullable=True)  # What ROPIAS predicted
    prediction_correct = db.Column(db.Boolean, nullable=True)   # Did prediction match reality?


class APICache(db.Model):
    """
    Caches NASA POWER API responses to avoid redundant API calls.
    TTL: 48 hours (NASA data latency).
    """
    __tablename__ = "api_cache"

    id           = db.Column(db.Integer, primary_key=True)
    cache_key    = db.Column(db.String(200), unique=True, nullable=False)
    fetched_at   = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at   = db.Column(db.DateTime, nullable=False)
    payload      = db.Column(db.Text, nullable=False)  # JSON string

class SystemSetting(db.Model):
    """
    Global configuration for ROPIAS logic (e.g. onset thresholds).
    Managed strictly by Admin users.
    """
    __tablename__ = "system_settings"
    id          = db.Column(db.Integer, primary_key=True)
    key_name    = db.Column(db.String(50), unique=True, nullable=False)
    key_value   = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Location(db.Model):
    """
    Managed locations (Cities/Towns) created by Admins to populate dropdowns easily.
    """
    __tablename__ = "managed_locations"
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    region      = db.Column(db.String(100), nullable=False)
    latitude    = db.Column(db.Float, nullable=False)
    longitude   = db.Column(db.Float, nullable=False)
