"""
officer_routes.py
==================
All routes for admin/extension officer users.
Every route is decorated with @admin_required.
This file expanded to support the full 16-page officer command centre.
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, Response
from flask_login import login_required, current_user
from auth.auth import admin_required
from database.models import db, User, QueryLog, AlertLog, SystemSetting, Location, AuditLog, ThresholdHistory, FieldNote
from datetime import datetime, timedelta
import json, io, csv, sys, os

officer_bp = Blueprint("officer", __name__, url_prefix="/officer")


# ──────────────────────────────────────────────────────────
# HELPER: count pending
# ──────────────────────────────────────────────────────────
def _pending_count():
    return User.query.filter_by(role="farmer", status="pending").count()

def _pending_list():
    return User.query.filter_by(role="farmer", status="pending").order_by(User.created_at.desc()).limit(5).all()


# ──────────────────────────────────────────────────────────
# PAGE 1: OVERVIEW DASHBOARD
# ──────────────────────────────────────────────────────────
@officer_bp.route("/")
@officer_bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    farmers = User.query.filter_by(role="farmer", is_active=True).all()
    true_onsets  = QueryLog.query.filter_by(onset_result="True Onset").count()
    false_onsets = QueryLog.query.filter_by(onset_result="False Onset").count()

    recent_queries = (
        QueryLog.query
        .order_by(QueryLog.created_at.desc())
        .limit(10).all()
    )

    now = datetime.utcnow()
    hour = now.hour
    greeting_time = "Morning" if hour < 12 else ("Afternoon" if hour < 17 else "Evening")

    return render_template(
        "officer/dashboard.html",
        stats={
            "active_farmers":  len(farmers),
            "true_onsets":     true_onsets,
            "false_onsets":    false_onsets,
            "alerts_sent":     AlertLog.query.count(),
            "total_queries":   QueryLog.query.count(),
        },
        pending_count       = _pending_count(),
        pending_farmers     = _pending_list(),
        recent_queries      = recent_queries,
        greeting_time       = greeting_time,
        today_str           = now.strftime("%B %d, %Y"),
    )


# ──────────────────────────────────────────────────────────
# PAGE 2: ALL FARMERS
# ──────────────────────────────────────────────────────────
@officer_bp.route("/farmers")
@login_required
@admin_required
def farmer_list():
    farmers = User.query.filter_by(role="farmer").order_by(User.created_at.desc()).all()
    return render_template(
        "officer/farmers.html",
        farmers=farmers,
        pending_count=_pending_count()
    )


# ──────────────────────────────────────────────────────────
# FARMER DETAIL PAGE
# ──────────────────────────────────────────────────────────
@officer_bp.route("/farmers/<int:user_id>")
@login_required
@admin_required
def farmer_detail(user_id):
    farmer = User.query.get_or_404(user_id)
    recent_queries = (
        QueryLog.query.filter_by(user_id=farmer.id)
        .order_by(QueryLog.created_at.desc()).limit(5).all()
    )
    recent_alerts = (
        AlertLog.query.filter_by(user_id=farmer.id)
        .order_by(AlertLog.sent_at.desc()).limit(5).all()
    )
    total_queries = QueryLog.query.filter_by(user_id=farmer.id).count()
    return render_template(
        "officer/farmer_detail.html",
        farmer=farmer,
        recent_queries=recent_queries,
        recent_alerts=recent_alerts,
        total_queries=total_queries,
        pending_count=_pending_count()
    )


# ──────────────────────────────────────────────────────────
# TOGGLE FARMER ACTIVE STATE
# ──────────────────────────────────────────────────────────
@officer_bp.route("/farmers/<int:user_id>/toggle", methods=["POST"])
@login_required
@admin_required
def toggle_farmer(user_id):
    farmer = User.query.get_or_404(user_id)
    if farmer.is_seeded:
        flash("Seeded accounts cannot be deactivated.", "warning")
        return redirect(url_for("officer.farmer_list"))
    farmer.is_active = not farmer.is_active
    db.session.commit()
    # Audit log
    _audit(action="FARMER_" + ("ACTIVATED" if farmer.is_active else "DEACTIVATED"),
           details=f"{farmer.full_name} ({farmer.email})")
    status = "activated" if farmer.is_active else "deactivated"
    flash(f"{farmer.full_name} has been {status}.", "success")
    return redirect(request.referrer or url_for("officer.farmer_list"))


# ──────────────────────────────────────────────────────────
# PAGE 3: REGISTER FARMER
# ──────────────────────────────────────────────────────────
@officer_bp.route("/farmers/new", methods=["GET", "POST"])
@login_required
@admin_required
def new_farmer():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email     = request.form.get("email", "").strip().lower()
        phone     = request.form.get("phone", "").strip()
        region    = request.form.get("region", "").strip()
        crop      = request.form.get("crop", "maize")
        password  = request.form.get("password", "")
        lat_str   = request.form.get("latitude", "").strip()
        lon_str   = request.form.get("longitude", "").strip()

        # Validate
        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "danger")
            return render_template("officer/new_farmer.html", pending_count=_pending_count())

        initials = "".join([n[0].upper() for n in full_name.split()[:2]])
        flat = float(lat_str) if lat_str else None
        flon = float(lon_str) if lon_str else None

        user = User(
            full_name      = full_name,
            username       = email.split("@")[0],
            email          = email,
            phone          = phone,
            role           = "farmer",
            status         = "approved",   # officer-created = auto-approved
            is_active      = True,
            farm_latitude  = flat,
            farm_longitude = flon,
            preferred_crop = crop,
            region         = region,
            avatar_initials= initials,
            greeting       = f"Habari, {full_name.split()[0]}!"
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        _audit(action="FARMER_REGISTERED", details=f"{full_name} ({email}) by officer")

        # Send credentials if requested
        if request.form.get("send_credentials") == "on" and phone:
            try:
                from src.whatsapp_alerts import send_message
                msg = f"✅ *ROPIAS Account Created*\n\nHello {full_name.split()[0]},\n\nYour ROPIAS account is ready!\n\n📧 Email: {email}\n🔑 Password: {password}\n\nVisit the dashboard to run your first analysis."
                send_message(phone, msg)
            except Exception as e:
                print(f"Credential WhatsApp failed: {e}")

        flash(f"Farmer account created for {full_name}.", "success")
        return redirect(url_for("officer.farmer_list"))
    return render_template("officer/new_farmer.html", pending_count=_pending_count())


# ──────────────────────────────────────────────────────────
# PAGE (APPROVAL): PENDING FARMERS
# ──────────────────────────────────────────────────────────
@officer_bp.route("/farmers/pending")
@login_required
@admin_required
def pending_farmers():
    pending = User.query.filter_by(role="farmer", status="pending").order_by(User.created_at.desc()).all()
    return render_template("officer/pending_farmers.html", pending=pending, pending_count=len(pending))


@officer_bp.route("/farmers/<int:user_id>/approve", methods=["POST"])
@login_required
@admin_required
def approve_farmer(user_id):
    farmer = User.query.get_or_404(user_id)
    farmer.status = "approved"
    farmer.is_active = True
    farmer.approved_by = current_user.id
    farmer.approved_at = datetime.utcnow()
    db.session.commit()
    _audit("FARMER_APPROVED", f"{farmer.full_name} ({farmer.email})")
    if farmer.phone:
        try:
            from src.whatsapp_alerts import send_approval_notification
            send_approval_notification(farmer.phone, farmer.full_name.split()[0])
        except Exception as e:
            print(f"Approval WhatsApp failed: {e}")
    flash(f"{farmer.full_name} approved successfully.", "success")
    return redirect(url_for("officer.pending_farmers"))


@officer_bp.route("/farmers/<int:user_id>/reject", methods=["POST"])
@login_required
@admin_required
def reject_farmer(user_id):
    farmer = User.query.get_or_404(user_id)
    reason = request.form.get("reason", "No reason provided")
    farmer.status = "rejected"
    farmer.is_active = False
    farmer.rejection_reason = reason
    db.session.commit()
    _audit("FARMER_REJECTED", f"{farmer.full_name}: {reason}")
    if farmer.phone:
        try:
            from src.whatsapp_alerts import send_message
            msg = f"❌ *ROPIAS Registration Update*\n\nHello {farmer.full_name.split()[0]},\n\nYour ROPIAS registration could not be approved. Reason: {reason}.\n\nContact your local extension officer for assistance."
            send_message(farmer.phone, msg)
        except Exception as e:
            print(f"Rejection WhatsApp failed: {e}")
    flash(f"{farmer.full_name} has been rejected.", "danger")
    return redirect(url_for("officer.pending_farmers"))


# ──────────────────────────────────────────────────────────
# PAGE 4: FARM MAP
# ──────────────────────────────────────────────────────────
@officer_bp.route("/map")
@login_required
@admin_required
def farm_map():
    return render_template("officer/farm_map.html", pending_count=_pending_count())


# ──────────────────────────────────────────────────────────
# PAGE 5: RUN ANALYSIS
# ──────────────────────────────────────────────────────────
@officer_bp.route("/analyze", methods=["GET"])
@login_required
@admin_required
def run_analysis():
    farmers = User.query.filter_by(role="farmer", is_active=True).filter(User.farm_latitude != None).all()
    return render_template("officer/run_analysis.html", farmers=farmers, pending_count=_pending_count())


# Field Note API
@officer_bp.route("/api/field-note", methods=["POST"])
@login_required
@admin_required
def save_field_note():
    body = request.get_json()
    note_text = body.get("note", "").strip()
    if not note_text:
        return jsonify({"error": "Note cannot be empty"}), 400
    note = FieldNote(
        officer_id=current_user.id,
        note=note_text
    )
    db.session.add(note)
    db.session.commit()
    return jsonify({"success": True, "id": note.id})


# ──────────────────────────────────────────────────────────
# PAGE 6: REGIONAL REPORTS
# ──────────────────────────────────────────────────────────
@officer_bp.route("/reports")
@login_required
@admin_required
def regional_reports():
    return render_template("officer/reports.html", pending_count=_pending_count())


# ──────────────────────────────────────────────────────────
# PAGE 7: MULTI-FARM COMPARE
# ──────────────────────────────────────────────────────────
@officer_bp.route("/compare")
@login_required
@admin_required
def compare_farms():
    farmers = User.query.filter_by(role="farmer", is_active=True).filter(User.farm_latitude != None).all()
    return render_template("officer/compare.html", farmers=farmers, pending_count=_pending_count())


# ──────────────────────────────────────────────────────────
# PAGE 8: SEASONAL CALENDAR
# ──────────────────────────────────────────────────────────
@officer_bp.route("/calendar")
@login_required
@admin_required
def seasonal_calendar():
    seasons = [
        {
            "name": "Long Rains (MAR–JUN)",
            "months": "March · April · May · June",
            "regions": "Western Kenya, Rift Valley, Nyanza",
            "icon": "🌧",
            "color": "var(--green-safe)",
            "description": "The primary planting season. Maximum rainfall, highest ROPIAS advisory activity.",
            "crops": ["Maize", "Beans", "Sorghum", "Sunflower", "Kale"],
        },
        {
            "name": "Short Rains (OCT–NOV)",
            "months": "October · November",
            "regions": "Eastern Kenya, Coast, Southern Rift",
            "icon": "🌦",
            "color": "var(--teal)",
            "description": "Secondary planting season. Shorter window with faster decision-making required.",
            "crops": ["Beans", "Cowpea", "Green Gram", "Sorghum"],
        },
        {
            "name": "Long Dry Season (JUL–SEP)",
            "months": "July · August · September",
            "regions": "All Kenya",
            "icon": "☀",
            "color": "var(--amber-watch)",
            "description": "Dry season. Monitor soil moisture for irrigated farms. Plan next season.",
            "crops": ["Tea", "Coffee", "Sugarcane (irrigated)"],
        },
        {
            "name": "Short Dry Season (JAN–FEB)",
            "months": "January · February",
            "regions": "All Kenya",
            "icon": "🔆",
            "color": "var(--text-muted)",
            "description": "Post-harvest dry period. Good time for land preparation and farmer registration.",
            "crops": ["Land preparation", "Farm planning"],
        },
    ]
    return render_template("officer/calendar.html", seasons=seasons, pending_count=_pending_count())


# ──────────────────────────────────────────────────────────
# PAGE 9: ALERT CENTRE
# ──────────────────────────────────────────────────────────
@officer_bp.route("/alerts", methods=["GET"])
@login_required
@admin_required
def alert_log():
    farmers = User.query.filter_by(role="farmer", is_active=True).all()
    recent_alerts = AlertLog.query.order_by(AlertLog.sent_at.desc()).limit(30).all()
    stats = {
        "total_sent": AlertLog.query.count(),
        "delivered": AlertLog.query.filter_by(delivery_status="delivered").count(),
        "failed": AlertLog.query.filter_by(delivery_status="failed").count(),
    }
    return render_template(
        "officer/alerts.html",
        farmers=farmers,
        recent_alerts=recent_alerts,
        stats=stats,
        pending_count=_pending_count()
    )


@officer_bp.route("/alerts/send", methods=["POST"])
@login_required
@admin_required
def send_alert():
    alert_type = request.form.get("alert_type")
    message    = request.form.get("message", "").strip()
    if not message:
        flash("Message cannot be empty.", "danger")
        return redirect(url_for("officer.alert_log"))

    try:
        from src.whatsapp_alerts import send_message
    except ImportError:
        flash("WhatsApp module not available.", "warning")
        return redirect(url_for("officer.alert_log"))

    if alert_type == "individual":
        farmer_id = request.form.get("farmer_id")
        if not farmer_id:
            flash("Select a farmer.", "danger")
            return redirect(url_for("officer.alert_log"))
        farmer = User.query.get(int(farmer_id))
        if farmer and farmer.phone:
            result = send_message(farmer.phone, message)
            log = AlertLog(
                user_id=farmer.id,
                channel="whatsapp",
                content_summary=message[:200],
                delivery_status="sent"
            )
            db.session.add(log)
            db.session.commit()
            _audit("ALERT_SENT", f"To {farmer.full_name}: {message[:80]}")
            flash(f"Alert sent to {farmer.full_name}.", "success")

    elif alert_type == "broadcast":
        farmers = User.query.filter_by(role="farmer", is_active=True).all()
        sent = 0
        for f in farmers:
            if f.phone and f.whatsapp_alerts:
                send_message(f.phone, f"📢 *ROPIAS Advisory*\n\n{message}")
                sent += 1
        _audit("BROADCAST_SENT", f"To {sent} farmers: {message[:80]}")
        flash(f"Broadcast sent to {sent} active farmers.", "success")

    return redirect(url_for("officer.alert_log"))


# ──────────────────────────────────────────────────────────
# MESSAGE LOG
# ──────────────────────────────────────────────────────────
@officer_bp.route("/messages")
@login_required
@admin_required
def message_log():
    alerts = AlertLog.query.order_by(AlertLog.sent_at.desc()).limit(200).all()
    return render_template("officer/message_log.html", alerts=alerts, pending_count=_pending_count())


# ──────────────────────────────────────────────────────────
# PAGE 10: ANALYTICS
# ──────────────────────────────────────────────────────────
@officer_bp.route("/analytics")
@login_required
@admin_required
def analytics():
    from collections import Counter
    from datetime import date

    total_queries = QueryLog.query.count()
    true_onsets   = QueryLog.query.filter_by(onset_result="True Onset").count()
    false_onsets  = QueryLog.query.filter_by(onset_result="False Onset").count()
    uncertain     = total_queries - true_onsets - false_onsets
    active_farmers = User.query.filter_by(role="farmer", is_active=True).count()

    true_pct  = round(true_onsets  / total_queries * 100, 1) if total_queries else 0
    false_pct = round(false_onsets / total_queries * 100, 1) if total_queries else 0

    # Monthly activity (last 6 months)
    monthly_labels, monthly_data = [], []
    for i in range(5, -1, -1):
        month_start = datetime.utcnow().replace(day=1) - timedelta(days=i*30)
        label = month_start.strftime("%b")
        cnt = QueryLog.query.filter(
            QueryLog.created_at >= month_start,
            QueryLog.created_at < month_start + timedelta(days=31)
        ).count()
        monthly_labels.append(label)
        monthly_data.append(cnt)

    # Crop distribution
    all_farmers = User.query.filter_by(role="farmer").all()
    crop_count = Counter(f.preferred_crop for f in all_farmers if f.preferred_crop)
    crop_labels = list(crop_count.keys())[:8]
    crop_data   = [crop_count[c] for c in crop_labels]

    # Soil moisture trend (last 14 days from QueryLog)
    recent_qs = QueryLog.query.order_by(QueryLog.created_at.desc()).limit(14).all()
    recent_qs.reverse()
    moisture_labels = [q.created_at.strftime("%b %d") for q in recent_qs]
    moisture_data   = [round(q.moisture_pct, 1) if q.moisture_pct else None for q in recent_qs]

    stats = {
        "total_queries": total_queries,
        "active_farmers": active_farmers,
        "true_onsets": true_onsets,
        "false_onsets": false_onsets,
        "uncertain_onsets": uncertain,
        "true_pct": true_pct,
        "false_pct": false_pct,
    }
    return render_template(
        "officer/analytics.html",
        stats=stats,
        monthly_labels=monthly_labels, monthly_data=monthly_data,
        crop_labels=crop_labels, crop_data=crop_data,
        moisture_labels=moisture_labels, moisture_data=moisture_data,
        pending_count=_pending_count()
    )


# ──────────────────────────────────────────────────────────
# PAGE 11: NASA DATA EXPLORER
# ──────────────────────────────────────────────────────────
@officer_bp.route("/nasa-explorer")
@login_required
@admin_required
def nasa_explorer():
    return render_template("officer/nasa_explorer.html", pending_count=_pending_count())


# ──────────────────────────────────────────────────────────
# PAGE 12: EXPORT CENTRE
# ──────────────────────────────────────────────────────────
@officer_bp.route("/export")
@login_required
@admin_required
def export_centre():
    return render_template("officer/export.html", pending_count=_pending_count())


@officer_bp.route("/export/farmers.csv")
@login_required
@admin_required
def export_farmers_csv():
    farmers = User.query.filter_by(role="farmer").all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Name", "Email", "Phone", "Region", "Crop", "Latitude", "Longitude", "Status", "WhatsApp", "Joined"])
    for f in farmers:
        writer.writerow([
            f.full_name, f.email, f.phone or "",
            f.region or "", f.preferred_crop or "",
            f.farm_latitude or "", f.farm_longitude or "",
            f.status, "Yes" if f.whatsapp_alerts else "No",
            f.created_at.strftime("%Y-%m-%d") if f.created_at else ""
        ])
    _audit("EXPORT_FARMERS_CSV", f"{len(farmers)} records")
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=ropias_farmers.csv"})


@officer_bp.route("/export/queries.csv")
@login_required
@admin_required
def export_queries_csv():
    queries = QueryLog.query.order_by(QueryLog.created_at.desc()).all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Date", "Farmer", "Crop", "Latitude", "Longitude", "Onset Result", "Soil %", "Irrigation Status"])
    for q in queries:
        writer.writerow([
            q.created_at.strftime("%Y-%m-%d %H:%M") if q.created_at else "",
            q.user.full_name if q.user else "Anonymous",
            q.crop_key or "", q.latitude, q.longitude,
            q.onset_result or "", round(q.moisture_pct, 1) if q.moisture_pct else "",
            q.irrigation_status or ""
        ])
    _audit("EXPORT_QUERIES_CSV", f"{len(queries)} records")
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=ropias_analyses.csv"})


@officer_bp.route("/export/alerts.csv")
@login_required
@admin_required
def export_alerts_csv():
    alerts = AlertLog.query.order_by(AlertLog.sent_at.desc()).all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Date", "Farmer", "Channel", "Message", "Status"])
    for a in alerts:
        writer.writerow([
            a.sent_at.strftime("%Y-%m-%d %H:%M") if a.sent_at else "",
            a.user.full_name if a.user else "Broadcast",
            a.channel or "", a.content_summary or "", a.delivery_status or ""
        ])
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=ropias_alerts.csv"})


@officer_bp.route("/export/report.pdf")
@login_required
@admin_required
def export_pdf_report():
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(72, 780, "ROPIAS Regional Advisory Report")
        c.setFont("Helvetica", 12)
        c.drawString(72, 755, f"Generated: {datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')}")
        c.drawString(72, 735, f"Officer: {current_user.full_name}")
        c.drawString(72, 715, f"Active Farmers: {User.query.filter_by(role='farmer', is_active=True).count()}")
        c.drawString(72, 695, f"Total Analyses: {QueryLog.query.count()}")
        c.drawString(72, 675, f"True Onsets: {QueryLog.query.filter_by(onset_result='True Onset').count()}")
        c.drawString(72, 655, f"False Onsets: {QueryLog.query.filter_by(onset_result='False Onset').count()}")
        c.save()
        buf.seek(0)
        return Response(buf.getvalue(), mimetype="application/pdf",
                        headers={"Content-Disposition": f"attachment; filename=ropias_report_{datetime.utcnow().strftime('%Y%m%d')}.pdf"})
    except ImportError:
        flash("PDF generation requires 'reportlab'. Run: pip install reportlab", "warning")
        return redirect(url_for("officer.export_centre"))


# ──────────────────────────────────────────────────────────
# PAGE 13: QUERY HISTORY
# ──────────────────────────────────────────────────────────
@officer_bp.route("/queries")
@login_required
@admin_required
def query_log():
    queries = QueryLog.query.order_by(QueryLog.created_at.desc()).limit(200).all()
    total = QueryLog.query.count()
    return render_template("officer/query_history.html", queries=queries, total=total, pending_count=_pending_count())


# ──────────────────────────────────────────────────────────
# PAGE 14: SYSTEM SETTINGS
# ──────────────────────────────────────────────────────────
@officer_bp.route("/system", methods=["GET", "POST"])
@login_required
@admin_required
def system_status():
    # Load config from SystemSetting table
    def get_setting(key, default=None):
        s = SystemSetting.query.filter_by(key=key).first()
        return s.value if s else default

    if request.method == "POST":
        flash("Threshold settings page is under construction.", "info")
        return redirect(url_for("officer.system_status"))

    officers = User.query.filter_by(role="admin").all()
    config = {
        "rainfall_threshold": get_setting("rainfall_threshold", 20),
        "dry_spell_days": get_setting("dry_spell_days", 7),
        "soil_min": get_setting("soil_min", 30),
        "lookback_days": get_setting("lookback_days", 60),
    }
    twilio_status = bool(os.environ.get("TWILIO_ACCOUNT_SID"))
    return render_template(
        "officer/settings.html",
        config=config, officers=officers,
        twilio_status=twilio_status,
        pending_count=_pending_count()
    )


@officer_bp.route("/system/thresholds", methods=["POST"])
@login_required
@admin_required
def save_thresholds():
    fields = ["rainfall_threshold", "dry_spell_days", "soil_min", "lookback_days"]
    for field in fields:
        val = request.form.get(field)
        if val:
            existing = SystemSetting.query.filter_by(key=field).first()
            old_val = existing.value if existing else None
            if existing:
                existing.value = val
            else:
                db.session.add(SystemSetting(key=field, value=val))
            # Record in ThresholdHistory
            hist = ThresholdHistory(changed_by=current_user.id, parameter=field, old_value=str(old_val), new_value=str(val))
            db.session.add(hist)
    db.session.commit()
    _audit("THRESHOLD_CHANGED", f"Updated: {', '.join(fields)}")
    flash("Threshold settings saved successfully.", "success")
    return redirect(url_for("officer.system_status"))


# ──────────────────────────────────────────────────────────
# PAGE 15: AUDIT LOG
# ──────────────────────────────────────────────────────────
@officer_bp.route("/audit")
@login_required
@admin_required
def audit_log_page():
    entries = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(200).all()
    return render_template("officer/audit_log.html", entries=entries, pending_count=_pending_count())


# ──────────────────────────────────────────────────────────
# PAGE 16: SYSTEM HEALTH
# ──────────────────────────────────────────────────────────
@officer_bp.route("/health")
@login_required
@admin_required
def system_health():
    import time

    # Check each service
    services = []

    # Flask DB
    try:
        User.query.count()
        services.append({"name": "Database", "icon": "🗄️", "status": "ok", "status_label": "CONNECTED", "detail": "SQLite / PostgreSQL connected."})
    except Exception as e:
        services.append({"name": "Database", "icon": "🗄️", "status": "error", "status_label": "ERROR", "detail": str(e)})

    # NASA API
    try:
        import urllib.request
        start = time.time()
        urllib.request.urlopen("https://power.larc.nasa.gov/api/temporal/daily/point?parameters=PRECTOTCORR&community=AG&longitude=36&latitude=0&format=JSON&start=20240101&end=20240102", timeout=5)
        lat = round((time.time() - start) * 1000, 0)
        services.append({"name": "NASA POWER API", "icon": "🛰️", "status": "ok", "status_label": "OPERATIONAL", "detail": "Live data endpoint reachable.", "latency": f"{lat}ms"})
    except Exception:
        services.append({"name": "NASA POWER API", "icon": "🛰️", "status": "warn", "status_label": "TIMEOUT", "detail": "Unable to reach NASA API. May be a network issue."})

    # Twilio
    twilio_ok = bool(os.environ.get("TWILIO_ACCOUNT_SID"))
    services.append({
        "name": "Twilio WhatsApp", "icon": "📱",
        "status": "ok" if twilio_ok else "warn",
        "status_label": "CONFIGURED" if twilio_ok else "NOT SET",
        "detail": "Credentials loaded from .env." if twilio_ok else "TWILIO_ACCOUNT_SID not in environment."
    })

    # Flask App
    services.append({"name": "Flask App", "icon": "⚙️", "status": "ok", "status_label": "RUNNING", "detail": f"ROPIAS ML Edition · Officer Panel"})

    # DB stats
    db_stats = [
        {"label": "Farmers", "count": User.query.filter_by(role="farmer").count()},
        {"label": "Analyses", "count": QueryLog.query.count()},
        {"label": "Alerts Sent", "count": AlertLog.query.count()},
        {"label": "Audit Entries", "count": AuditLog.query.count()},
        {"label": "Field Notes", "count": FieldNote.query.count()},
    ]

    import platform, sys
    env_info = {
        "Python Version": sys.version.split()[0],
        "Platform": platform.system(),
        "Flask Mode": os.environ.get("FLASK_ENV", "development").title(),
        "Database": "PostgreSQL" if "postgresql" in os.environ.get("DATABASE_URL", "") else "SQLite",
        "Server Time (UTC)": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    }

    return render_template(
        "officer/system_health.html",
        services=services, db_stats=db_stats, env_info=env_info,
        pending_count=_pending_count()
    )


# ──────────────────────────────────────────────────────────
# PENDING APPROVALS API ENDPOINT
# ──────────────────────────────────────────────────────────
@officer_bp.route("/api/pending-count")
@login_required
@admin_required
def api_pending_count():
    return jsonify({"count": _pending_count()})


# ──────────────────────────────────────────────────────────
# AUDIT LOG HELPER
# ──────────────────────────────────────────────────────────
def _audit(action: str, details: str = None):
    try:
        entry = AuditLog(
            user_id=current_user.id if current_user.is_authenticated else None,
            action=action,
            details=details,
            ip_address=request.remote_addr if request else None,
            timestamp=datetime.utcnow()
        )
        db.session.add(entry)
        db.session.commit()
    except Exception as e:
        print(f"Audit log failed: {e}")
