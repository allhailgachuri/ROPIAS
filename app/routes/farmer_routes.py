"""
farmer_routes.py
=================
All routes accessible only to farmer-role users.
Every route decorated with @farmer_required.
"""

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from auth.auth import farmer_required
from database.models import db, QueryLog
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from data_fetcher import fetch_climate_data, validate_kenya_coordinates
from onset_engine import classify_onset
from irrigation_engine import classify_soil_moisture
from crop_registry import get_crop, get_crops_by_category

farmer_bp = Blueprint("farmer", __name__)


@farmer_bp.route("/dashboard")
@login_required
@farmer_required
def dashboard():
    """
    Main farmer dashboard.
    Pre-populates with farmer's saved GPS coordinates and preferred crop.
    """
    crops_by_category = get_crops_by_category()
    return render_template(
        "farmer/dashboard.html",
        user=current_user,
        crops_by_category=crops_by_category,
        saved_lat=current_user.farm_latitude or "",
        saved_lon=current_user.farm_longitude or "",
        saved_crop=current_user.preferred_crop or "maize"
    )


@farmer_bp.route("/profile", methods=["GET", "POST"])
@login_required
@farmer_required
def profile():
    """Farmer profile — update name, phone, GPS, crop, alert preferences."""
    if request.method == "POST":
        current_user.phone           = request.form.get("phone", current_user.phone)
        current_user.farm_latitude   = float(request.form.get("latitude") or 0) or None
        current_user.farm_longitude  = float(request.form.get("longitude") or 0) or None
        current_user.preferred_crop  = request.form.get("crop", current_user.preferred_crop)
        current_user.whatsapp_alerts = request.form.get("whatsapp_alerts") == "on"
        db.session.commit()
        from flask import flash
        flash("Profile updated successfully.", "success")
    return render_template("farmer/profile.html", user=current_user)


@farmer_bp.route("/history")
@login_required
@farmer_required
def history():
    """Shows the farmer's last 20 advisory results."""
    logs = (
        QueryLog.query
        .filter_by(user_id=current_user.id)
        .order_by(QueryLog.created_at.desc())
        .limit(20)
        .all()
    )
    return render_template("farmer/history.html", logs=logs, user=current_user)
