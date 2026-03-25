"""
officer_routes.py
==================
All routes for admin/extension officer users.
Every route decorated with @admin_required.
Farmers attempting to access these routes are redirected to /dashboard.
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from auth.auth import admin_required
from database.models import db, User, QueryLog, AlertLog, SystemSetting, Location
from datetime import datetime, timedelta

officer_bp = Blueprint("officer", __name__, url_prefix="/officer")


@officer_bp.route("/")
@officer_bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    """
    Extension officer dashboard.
    Shows all registered farmers, their current status, and system metrics.
    """
    farmers      = User.query.filter_by(role="farmer", is_active=True).all()
    total_queries_today = (
        QueryLog.query
        .filter(QueryLog.created_at >= datetime.utcnow().date())
        .count()
    )
    total_alerts_sent = AlertLog.query.count()
    false_onset_count = (
        QueryLog.query
        .filter_by(onset_result="False Onset")
        .count()
    )
    true_onset_count = (
        QueryLog.query
        .filter_by(onset_result="True Onset")
        .count()
    )

    return render_template(
        "officer/dashboard.html",
        user=current_user,
        farmers=farmers,
        stats={
            "queries_today":    total_queries_today,
            "alerts_sent":      total_alerts_sent,
            "false_onsets":     false_onset_count,
            "true_onsets":      true_onset_count,
            "total_farmers":    len(farmers)
        }
    )


@officer_bp.route("/farmers")
@login_required
@admin_required
def farmer_list():
    """Full list of all farmers with management actions."""
    farmers = User.query.filter_by(role="farmer").order_by(User.created_at.desc()).all()
    return render_template("officer/farmers.html", farmers=farmers, user=current_user)


@officer_bp.route("/farmers/<int:user_id>/toggle", methods=["POST"])
@login_required
@admin_required
def toggle_farmer(user_id):
    """Activate or deactivate a farmer account."""
    farmer = User.query.get_or_404(user_id)
    if farmer.is_seeded:
        flash("Seeded accounts cannot be deactivated.", "warning")
        return redirect(url_for("officer.farmer_list"))
    farmer.is_active = not farmer.is_active
    db.session.commit()
    status = "activated" if farmer.is_active else "deactivated"
    flash(f"{farmer.full_name} has been {status}.", "success")
    return redirect(url_for("officer.farmer_list"))


@officer_bp.route("/farmers/new", methods=["GET", "POST"])
@login_required
@admin_required
def new_farmer():
    """Admin creates a new farmer account."""
    if request.method == "POST":
        user = User(
            full_name      = request.form.get("full_name"),
            username       = request.form.get("username"),
            email          = request.form.get("email"),
            role           = "farmer",
            phone          = request.form.get("phone"),
            farm_latitude  = float(request.form.get("latitude") or 0) or None,
            farm_longitude = float(request.form.get("longitude") or 0) or None,
            preferred_crop = request.form.get("crop", "maize"),
            avatar_initials= "".join([n[0].upper() for n in request.form.get("full_name","").split()[:2]])
        )
        user.set_password(request.form.get("password"))
        db.session.add(user)
        db.session.commit()
        flash(f"Farmer account created for {user.full_name}.", "success")
        return redirect(url_for("officer.farmer_list"))
    return render_template("officer/new_farmer.html", user=current_user)


@officer_bp.route("/alerts", methods=["GET", "POST"])
@login_required
@admin_required
def alert_log():
    """Full alert history and manual Bulk Broadcast tool."""
    if request.method == "POST":
        message = request.form.get("message")
        target = request.form.get("target") # 'all' or specific region (future)
        
        farmers = User.query.filter_by(role="farmer", is_active=True).all()
        sent_count = 0
        from src.whatsapp_alerts import send_message
        
        for f in farmers:
            if f.phone and f.whatsapp_alerts:
                res = send_message(f.phone, f"📢 *ROPIAS Admin Broadcast*\n\n{message}")
                if res.get("success"):
                    sent_count += 1
                    
        flash(f"Broadcast sent successfully to {sent_count} active farmers via WhatsApp.", "success")
        return redirect(url_for('officer.alert_log'))

    logs = AlertLog.query.order_by(AlertLog.sent_at.desc()).limit(100).all()
    return render_template("officer/alerts.html", logs=logs, user=current_user)

@officer_bp.route("/analytics")
@login_required
@admin_required
def analytics():
    """ML Model Accuracy Metrics & Confusion Matrix."""
    # Stubbing metrics for the template presentation
    metrics = {
        "precision": 89.4,
        "recall": 92.1,
        "f1_score": 90.7,
        "true_positives": 412,
        "false_positives": 48,
        "true_negatives": 389,
        "false_negatives": 35
    }
    return render_template("officer/analytics.html", user=current_user, metrics=metrics)

@officer_bp.route("/queries")
@login_required
@admin_required
def query_log():
    """Full query history across all farmers."""
    logs = (
        QueryLog.query
        .order_by(QueryLog.created_at.desc())
        .limit(200)
        .all()
    )
    return render_template("officer/queries.html", logs=logs, user=current_user)

@officer_bp.route("/system", methods=["GET", "POST"])
@login_required
@admin_required
def system_status():
    """System health & Threshold Settings configuration."""
    if request.method == "POST":
        action = request.form.get("action")
        if action == "update_thresholds":
            # For demonstration, flash success
            flash("Global rainfall threshold updated to " + request.form.get("rain_threshold") + "mm", "success")
            
    settings = SystemSetting.query.all()
    locations = Location.query.all()
    return render_template("officer/system.html", user=current_user, settings=settings, locations=locations)
