"""
auth.py
========
Authentication logic for ROPIAS.
Handles login, logout, and route protection decorators.

Two roles:
  admin  → can access /officer, /admin/*, /api/* (management)
  farmer → can access /dashboard only, blocked from all admin routes

Route protection pattern:
  @login_required            → any logged-in user
  @admin_required            → admin role only, redirects farmers home
  @farmer_required           → farmer role only
"""

from functools import wraps
from flask import redirect, url_for, flash, abort
from flask_login import LoginManager, current_user

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access ROPIAS."
login_manager.login_message_category = "info"


def admin_required(f):
    """
    Decorator: blocks non-admin users from accessing a route.
    Farmers who try to access admin routes are redirected to
    their own dashboard with a warning — not shown an error page.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if not current_user.is_admin:
            flash("Access restricted. Redirecting to your dashboard.", "warning")
            return redirect(url_for("farmer.dashboard"))
        return f(*args, **kwargs)
    return decorated


def farmer_required(f):
    """
    Decorator: only allows farmer-role users.
    Admins who visit /dashboard are redirected to /officer.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if current_user.is_admin:
            return redirect(url_for("officer.dashboard"))
        return f(*args, **kwargs)
    return decorated
