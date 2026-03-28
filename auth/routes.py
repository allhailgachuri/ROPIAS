"""
auth/routes.py
===============
Login, logout, register, and password reset routes.
"""

from flask import (
    Blueprint, render_template, redirect,
    url_for, flash, request, current_app, session, jsonify
)
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
import re
from database.models import db, User
from src.whatsapp_alerts import send_new_registration_alert, send_password_reset
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def get_serializer():
    """Returns the token serializer bound to the app secret key."""
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Login page. Blocks users whose status is not 'approved' (except seeds).
    Redirects to proper dashboards dynamically.
    """
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password   = request.form.get("password", "").strip()
        remember   = request.form.get("remember") == "on"

        user = (
            User.query.filter_by(email=identifier).first() or
            User.query.filter_by(username=identifier).first()
        )

        if user and user.check_password(password):
            if not user.is_active:
                flash("This account has been deactivated. Contact your extension officer for assistance.", "danger")
                return render_template("auth/login.html")
            
            # Check strictly for pending farmers (ignoring seeds)
            if user.status == "pending" and not user.is_seeded:
                flash("Your account is pending approval by an extension officer. You will receive a WhatsApp message when approved.", "warning")
                return render_template("auth/login.html")
            
            if user.status == "rejected":
                flash(f"This account application was declined. Reason: {user.rejection_reason or 'Not provided'}", "danger")
                return render_template("auth/login.html")

            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()

            flash(user.greeting or f"Habari, {user.full_name}!", "success")

            next_page = request.args.get("next")
            if next_page and next_page.startswith("/"):
                return redirect(next_page)
            return _redirect_by_role(user)

        else:
            flash("Incorrect email or password. Please try again.", "danger")

    return render_template("auth/login.html")


def is_strong_password(password: str) -> bool:
    if len(password) < 8: return False
    if not re.search(r"[A-Z]", password): return False
    # if not re.search(r"[a-z]", password): return False # Relaxed lower req for edge devices
    if not re.search(r"\d", password): return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password): return False
    return True


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """
    Public registration. Step 1-3 multi-step form.
    Creates user with status='pending'.
    Notifies all admins via WhatsApp immediately.
    """
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        crop = request.form.get("crop", "maize").strip()
        region = request.form.get("region", "").strip()
        lat = request.form.get("latitude")
        lon = request.form.get("longitude")
        password = request.form.get("password", "")

        # Validation
        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists. Sign in instead.", "warning")
            return render_template("auth/register.html")

        if not is_strong_password(password):
            flash("Password must be 8+ chars and contain uppercase, number, and special character.", "danger")
            return render_template("auth/register.html")

        # Create unique username
        base_username = email.split("@")[0]
        username = base_username
        suffix = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{suffix}"
            suffix += 1
            
        initials = "".join([n[0].upper() for n in full_name.split()[:2]]) if full_name else "F"

        try:
            flat = float(lat) if lat else None
            flon = float(lon) if lon else None
        except ValueError:
            flat = flon = None

        new_user = User(
            full_name=full_name,
            username=username,
            email=email,
            phone=phone,
            role="farmer",
            status="pending",
            is_active=False,
            farm_latitude=flat,
            farm_longitude=flon,
            preferred_crop=crop,
            region=region,
            avatar_initials=initials,
            greeting=f"Habari, {full_name.split()[0]}!"
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        # Notify Admins via WhatsApp
        admins = User.query.filter_by(role="admin", is_active=True).all()
        for admin in admins:
            if admin.phone:
                # Fire and forget
                try:
                    send_new_registration_alert(
                        admin_phone=admin.phone,
                        admin_name=admin.full_name.split()[0],
                        farmer_name=new_user.full_name,
                        farmer_email=new_user.email,
                        farmer_phone=new_user.phone,
                        farmer_crop=new_user.preferred_crop,
                        farmer_region=new_user.region or "Not specified",
                        farmer_lat=new_user.farm_latitude or 0,
                        farmer_lon=new_user.farm_longitude or 0
                    )
                except Exception as e:
                    print(f"Failed to alert admin: {e}")

        # Note: We do NOT log them in. They see success screen natively.
        flash("Account created! Check WhatsApp for approval status.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """
    Accepts email. Generates reset token. Sends WhatsApp link.
    """
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        user = User.query.filter_by(email=email).first()
        
        if user and user.phone:
            s = get_serializer()
            # Token embedded with user ID
            token = s.dumps(user.email, salt="password-reset")
            user.reset_token = token
            user.reset_token_exp = datetime.utcnow() + timedelta(hours=1)
            user.reset_used = False
            db.session.commit()

            # The URL points to reset handler
            reset_url = url_for("auth.reset_password", token=token, _external=True)
            try:
                send_password_reset(user.phone, user.full_name.split()[0], reset_url)
            except Exception as e:
                print(f"Failed to send reset link: {e}")
                
        # Always report assumed success to prevent enumerations
        return jsonify({"status": "ok", "message": "If an account exists, a reset link was sent."})

    return render_template("auth/forgot_password.html")


@auth_bp.route("/reset/<token>", methods=["GET", "POST"])
def reset_password(token):
    """
    Validates token (1hr expiry, single use). Shows reset form if valid.
    """
    s = get_serializer()
    try:
        email = s.loads(token, salt="password-reset", max_age=3600)
    except SignatureExpired:
        flash("This reset link has expired. Request a new link.", "danger")
        return redirect(url_for("auth.forgot_password"))
    except BadTimeSignature:
        flash("Invalid token.", "danger")
        return redirect(url_for("auth.forgot_password"))

    user = User.query.filter_by(email=email, reset_token=token).first()
    if not user or user.reset_used:
        flash("This link has already been used. Your password was already reset.", "warning")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        password = request.form.get("password")
        if not is_strong_password(password):
            flash("Password too weak. Use capitals, numbers, and symbols.", "danger")
            return redirect(request.url)

        user.set_password(password)
        user.reset_used = True
        db.session.commit()
        flash("Password updated! Sign in with your new password.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", token=token)


@auth_bp.route("/login/google")
def login_google():
    flash("Google Sign-In integration requires active Developer credentials. Please use manual sign up.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/logout")
@login_required
def logout():
    name = current_user.full_name.split()[0]
    logout_user()
    session.clear()  # Wipe ALL session data — kills remember-me cookie
    flash(f"You've been signed out. See you next time, {name}! 🌧️", "info")
    return redirect(url_for("index"))  # Back to public landing page


@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        current_pw = request.form.get("current_password", "")
        new_pw     = request.form.get("new_password", "")
        confirm_pw = request.form.get("confirm_password", "")

        if not current_user.check_password(current_pw):
            flash("Current password is incorrect.", "danger")
        elif new_pw != confirm_pw:
            flash("New passwords do not match.", "danger")
        elif len(new_pw) < 8:
            flash("Password must be at least 8 characters.", "danger")
        else:
            current_user.set_password(new_pw)
            db.session.commit()
            flash("Password updated successfully.", "success")
            return _redirect_by_role(current_user)

    return render_template("auth/change_password.html")


def _redirect_by_role(user):
    if user.is_admin:
        return redirect(url_for("officer.dashboard"))
    return redirect(url_for("farmer.dashboard"))
