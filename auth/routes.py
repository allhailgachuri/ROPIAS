"""
auth/routes.py
===============
Login, logout, and password change routes.
"""

from flask import (
    Blueprint, render_template, redirect,
    url_for, flash, request, session
)
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
import re
from database.models import db, User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Login page. Redirects to role-appropriate dashboard on success.
    Admins → /officer
    Farmers → /dashboard
    """
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password   = request.form.get("password", "").strip()
        remember   = request.form.get("remember") == "on"

        # Allow login by email OR username
        user = (
            User.query.filter_by(email=identifier).first() or
            User.query.filter_by(username=identifier).first()
        )

        if user and user.is_active and user.check_password(password):
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()

            flash(user.greeting or f"Welcome back, {user.full_name}!", "success")

            # Honour the 'next' parameter if it exists and is safe
            next_page = request.args.get("next")
            if next_page and next_page.startswith("/"):
                return redirect(next_page)
            return _redirect_by_role(user)

        else:
            flash("Incorrect email or password. Please try again.", "danger")

    return render_template("auth/login.html")


def is_strong_password(password: str) -> bool:
    """
    Strict password policy:
    - At least 8 characters long
    - Contains at least 1 uppercase letter
    - Contains at least 1 lowercase letter
    - Contains at least 1 number
    - Contains at least 1 special character
    """
    if len(password) < 8: return False
    if not re.search(r"[A-Z]", password): return False
    if not re.search(r"[a-z]", password): return False
    if not re.search(r"\d", password): return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password): return False
    return True


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    """Manual Farmer Registration with strict password constraints."""
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        
        # Validation
        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "warning")
            return redirect(url_for("auth.signup"))
            
        if not is_strong_password(password):
            flash("Password must be 8+ chars and contain uppercase, lowercase, number, and special character.", "danger")
            return redirect(url_for("auth.signup"))
            
        # username generation
        base_username = email.split("@")[0]
        username = base_username
        suffix = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{suffix}"
            suffix += 1

        # Calculate initials securely
        initials = "".join([n[0].upper() for n in full_name.split()[:2]]) if full_name else "FR"

        # Create Farmer
        new_user = User(
            full_name=full_name,
            username=username,
            email=email,
            phone=phone,
            role="farmer",
            avatar_initials=initials,
            greeting=f"Habari {full_name.split()[0]}! Welcome to your ROPIAS dashboard."
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        # Auto-login
        login_user(new_user)
        flash("Registration successful! Welcome to ROPIAS.", "success")
        return redirect(url_for("farmer.dashboard"))

    return render_template("auth/signup.html")


@auth_bp.route("/login/google")
def login_google():
    """
    Initiates Google OAuth flow. 
    (Requires client integration via Authlib or OAuth2. 
    Placeholder pending GOOGLE_CLIENT_ID configuration validation).
    """
    flash("Google Sign-In integration requires active Google Developer credentials. Please use manual sign up for now.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/logout")
@login_required
def logout():
    """Logs the current user out and redirects to login page."""
    name = current_user.full_name
    logout_user()
    flash(f"You have been logged out, {name}. See you next time.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    """Allows any logged-in user to change their own password."""
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
    """Routes user to the correct dashboard based on their role."""
    if user.is_admin:
        return redirect(url_for("officer.dashboard"))
    return redirect(url_for("farmer.dashboard"))
