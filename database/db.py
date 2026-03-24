"""
db.py
======
SQLAlchemy database setup and ORM models for ROPIAS.
Handles interactions with SQLite (development) or PostgreSQL (production).
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Query(db.Model):
    """Stores every query a farmer makes for analytics."""
    __tablename__ = 'queries'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    onset_result = db.Column(db.String(50))
    onset_color = db.Column(db.String(20))
    moisture_pct = db.Column(db.Float)
    irrigation_status = db.Column(db.String(100))
    data_start = db.Column(db.String(20))
    data_end = db.Column(db.String(20))

class ApiCache(db.Model):
    """Stores cached NASA API JSON responses to avoid rate limits and reduce latency."""
    __tablename__ = 'api_cache'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cache_key = db.Column(db.String(200), unique=True, nullable=False) # e.g. "lat_lon_start_end_params"
    fetched_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    payload = db.Column(db.Text, nullable=False)

class AlertSubscription(db.Model):
    """Stores SMS alert subscriptions."""
    __tablename__ = 'alert_subscriptions'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    phone = db.Column(db.String(20), nullable=False, unique=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class HistoricalOnset(db.Model):
    """Stores historical validation records for ML training."""
    __tablename__ = 'historical_onsets'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    year = db.Column(db.Integer)
    season = db.Column(db.String(20))
    onset_date = db.Column(db.String(50))
    true_onset = db.Column(db.Boolean)
    system_result = db.Column(db.String(50))
    correct = db.Column(db.Boolean)
