"""
farmer_routes.py
=================
All routes accessible only to farmer-role users.
Every route decorated with @farmer_required.
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, Response
from flask_login import login_required, current_user
from auth.auth import farmer_required
from database.models import db, QueryLog
from datetime import datetime
import sys, os, csv, io
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
    """Shows the farmer's last 30 advisory results."""
    logs = (
        QueryLog.query
        .filter_by(user_id=current_user.id)
        .order_by(QueryLog.created_at.desc())
        .limit(30)
        .all()
    )
    total = QueryLog.query.filter_by(user_id=current_user.id).count()
    return render_template("farmer/history.html", logs=logs, user=current_user, total=min(total, 30))


@farmer_bp.route("/crops")
@login_required
@farmer_required
def crops():
    """Reference library for all Kenya crops with NASA stats."""
    crops_by_category = get_crops_by_category()
    nasa_stats = {}
    if current_user.farm_latitude and current_user.farm_longitude:
        try:
            climate = fetch_climate_data(
                current_user.farm_latitude,
                current_user.farm_longitude,
                days_back=30
            )
            rain = climate["precipitation"]
            soil = climate["soil_moisture"]
            soil_clean = soil.dropna()
            nasa_stats = {
                "total_rain_30d":   round(float(rain.sum()), 1),
                "avg_daily_rain":   round(float(rain.mean()), 2),
                "max_daily_rain":   round(float(rain.max()), 1),
                "current_moisture": round(float(soil_clean.iloc[-1]) * 100, 1) if len(soil_clean) > 0 else None,
                "dry_days_30":      int((rain < 1.0).sum()),
                "wet_days_30":      int((rain >= 1.0).sum()),
            }
        except Exception as e:
            print(f"NASA fetch for crops page failed: {e}")
            nasa_stats = {}
    return render_template("farmer/crops.html", crops_by_category=crops_by_category, nasa_stats=nasa_stats, user=current_user)


@farmer_bp.route("/settings", methods=["GET", "POST"])
@login_required
@farmer_required
def settings():
    """User settings — theme, language, notifications, data/privacy."""
    if request.method == "POST":
        action = request.form.get("action")
        if action == "notifications":
            current_user.whatsapp_alerts = request.form.get("whatsapp_alerts") == "on"
            db.session.commit()
            flash("Notification preferences saved.", "success")
        elif action == "default_crop":
            crop = request.form.get("default_crop")
            if crop:
                current_user.preferred_crop = crop
                db.session.commit()
                flash("Default crop updated.", "success")
        return redirect(url_for("farmer.settings"))
    return render_template("farmer/settings.html", user=current_user)


@farmer_bp.route("/download-history")
@login_required
@farmer_required
def download_history():
    """Export all QueryLog entries as CSV."""
    logs = QueryLog.query.filter_by(user_id=current_user.id).order_by(QueryLog.created_at.desc()).all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Date", "Crop", "Latitude", "Longitude", "Onset Result", "Moisture %", "Irrigation Status"])
    for log in logs:
        writer.writerow([
            log.created_at.strftime("%Y-%m-%d %H:%M"),
            log.crop_key or "",
            log.latitude, log.longitude,
            log.onset_result or "",
            round(log.moisture_pct, 1) if log.moisture_pct else "",
            log.irrigation_status or ""
        ])
    output = buf.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=ropias_history_{current_user.id}.csv"}
    )


@farmer_bp.route("/clear-history", methods=["POST"])
@login_required
@farmer_required
def clear_history():
    """Delete all QueryLog entries for this user."""
    QueryLog.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash("Your analysis history has been cleared.", "info")
    return redirect(url_for("farmer.settings"))

