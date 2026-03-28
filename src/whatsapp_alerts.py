"""
whatsapp_alerts.py
===================
Handles all Twilio WhatsApp messaging for ROPIAS.

Message types:
  - onset_alert:      True/False onset advisory
  - irrigation_alert: Soil moisture irrigation advisory
  - welcome:          New farmer registration welcome
  - daily_digest:     Morning summary (called by scheduler at 6am)

Incoming message handling:
  - STATUS  → triggers fresh analysis for farmer's saved coordinates
  - NO RAIN → stores ground-truth feedback in FarmFeedback table
  - STOP    → sets whatsapp_alerts = False for the farmer
  - START   → sets whatsapp_alerts = True for the farmer
"""

import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN   = os.getenv("TWILIO_AUTH_TOKEN")
FROM_NUMBER  = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")


def get_client() -> Client:
    """Returns an authenticated Twilio REST client."""
    return Client(ACCOUNT_SID, AUTH_TOKEN)


def format_number(phone: str) -> str:
    """
    Normalises any Kenyan phone number format to whatsapp:+254XXXXXXXXX.
    Accepts: 0798639575, 254798639575, +254798639575
    """
    phone = phone.strip().replace(" ", "")
    if phone.startswith("whatsapp:"):
        return phone
    if phone.startswith("0"):
        phone = "+254" + phone[1:]
    elif phone.startswith("254") and not phone.startswith("+"):
        phone = "+" + phone
    elif not phone.startswith("+"):
        phone = "+" + phone
    return f"whatsapp:{phone}"


def send_message(to: str, body: str) -> dict:
    """
    Core send function. All other send_* functions call this.
    Returns dict with success bool, message_sid, and status.
    """
    try:
        client = get_client()
        msg = client.messages.create(
            body=body,
            from_=FROM_NUMBER,
            to=format_number(to)
        )
        return {
            "success": True,
            "message_sid": msg.sid,
            "status": msg.status,
            "to": to
        }
    except Exception as e:
        return {"success": False, "error": str(e), "to": to}


def send_onset_alert(phone, farmer_name, crop_name, onset_result, onset_summary):
    """Sends a True/False onset advisory WhatsApp message."""
    icons = {
        "True Onset":         "✅",
        "False Onset":        "🚨",
        "No Onset Detected":  "⏳",
        "Insufficient Data":  "⚠️"
    }
    icon = icons.get(onset_result, "🌧️")
    body = (
        f"*ROPIAS Advisory — {farmer_name}*\n\n"
        f"{icon} *{onset_result}*\n"
        f"Crop: {crop_name}\n\n"
        f"{onset_summary}\n\n"
        f"_Reply *STATUS* for a fresh analysis._\n"
        f"_Reply *NO RAIN* if it did not rain today._\n"
        f"_Reply *STOP* to unsubscribe._\n\n"
        f"— ROPIAS | NASA POWER Satellite Data"
    )
    return send_message(phone, body)


def send_irrigation_alert(phone, farmer_name, crop_name,
                          irrigation_status, moisture_percent, summary):
    """Sends an irrigation advisory WhatsApp message."""
    icons = {
        "Irrigate Today":                   "💧",
        "Soil Moisture Optimal":            "🌱",
        "Do Not Irrigate — Soil Saturated": "🌊"
    }
    icon = icons.get(irrigation_status, "💧")
    body = (
        f"*ROPIAS Irrigation Advisory*\n\n"
        f"{icon} *{irrigation_status}*\n"
        f"Farmer: {farmer_name} | Crop: {crop_name}\n"
        f"Soil Moisture: {moisture_percent}%\n\n"
        f"{summary}\n\n"
        f"— ROPIAS | NASA POWER Satellite Data"
    )
    return send_message(phone, body)


def send_welcome(phone, farmer_name):
    """Sends welcome message to a newly registered farmer."""
    body = (
        f"🌧️ *Welcome to ROPIAS, {farmer_name}!*\n\n"
        f"You will now receive daily planting and irrigation "
        f"advisories powered by NASA satellite data.\n\n"
        f"*Commands:*\n"
        f"• *STATUS* — get your current farm advisory\n"
        f"• *NO RAIN* — report that it did not rain today\n"
        f"• *STOP* — unsubscribe from alerts\n"
        f"• *START* — resubscribe\n\n"
        f"Alerts are sent every morning at 6:00 AM.\n\n"
        f"— ROPIAS | KCA University, Nairobi"
    )
    return send_message(phone, body)


def send_daily_digest(phone, farmer_name, crop_name,
                      onset_result, moisture_pct, irrigation_status):
    """
    Morning digest — a single combined message covering both
    onset status and irrigation advisory. Sent by the 6am scheduler.
    """
    onset_icons = {
        "True Onset": "✅", "False Onset": "🚨",
        "No Onset Detected": "⏳"
    }
    irr_icons = {
        "Irrigate Today": "💧",
        "Soil Moisture Optimal": "🌱",
        "Do Not Irrigate — Soil Saturated": "🌊"
    }
    body = (
        f"🌅 *Good morning, {farmer_name}!*\n"
        f"Your ROPIAS daily advisory:\n\n"
        f"{onset_icons.get(onset_result, '🌧️')} *Onset:* {onset_result}\n"
        f"{irr_icons.get(irrigation_status, '💧')} *Irrigation:* {irrigation_status}\n"
        f"Soil moisture: {moisture_pct}%\n"
        f"Crop: {crop_name}\n\n"
        f"_Reply STATUS for detailed report._\n"
        f"— ROPIAS"
    )
    return send_message(phone, body)


def send_password_reset(phone: str, name: str, reset_url: str) -> dict:
    """Sends a WhatsApp password reset link to the user."""
    body = (
        f"🔐 *ROPIAS Password Reset*\n\n"
        f"Hello {name},\n\n"
        f"Someone requested a password reset for your ROPIAS account.\n\n"
        f"Reset your password:\n{reset_url}\n\n"
        f"⏱️ This link expires in 1 hour.\n\n"
        f"If you didn't request this, ignore this message — "
        f"your account is safe.\n\n"
        f"— ROPIAS System"
    )
    return send_message(phone, body)


def send_new_registration_alert(
    admin_phone: str,
    admin_name: str,
    farmer_name: str,
    farmer_email: str,
    farmer_phone: str,
    farmer_crop: str,
    farmer_region: str,
    farmer_lat: float,
    farmer_lon: float
) -> dict:
    """
    Notifies an admin when a new farmer registers and needs approval.
    Sent to all admin users immediately on registration.
    """
    body = (
        f"👤 *New ROPIAS Registration*\n\n"
        f"Hello {admin_name},\n\n"
        f"A new farmer has registered and needs your approval:\n\n"
        f"*Name:* {farmer_name}\n"
        f"*Email:* {farmer_email}\n"
        f"*Phone:* {farmer_phone}\n"
        f"*Crop:* {farmer_crop}\n"
        f"*Region:* {farmer_region}\n"
        f"*Coordinates:* {farmer_lat}°N, {farmer_lon}°E\n\n"
        f"Approve or reject this account in the officer dashboard:\n"
        f"https://ropias.app/officer/farmers/pending\n\n"
        f"— ROPIAS System"
    )
    return send_message(admin_phone, body)


def send_approval_notification(phone: str, name: str) -> dict:
    """Notifies a farmer their account has been approved."""
    body = (
        f"✅ *ROPIAS Account Approved!*\n\n"
        f"Great news, {name}!\n\n"
        f"Your ROPIAS account has been approved by an extension officer.\n\n"
        f"You can now sign in and get your daily planting advisory:\n"
        f"https://ropias.app/auth/login\n\n"
        f"*Your first steps:*\n"
        f"1. Sign in with your email and password\n"
        f"2. Confirm your farm coordinates\n"
        f"3. Select your crop\n"
        f"4. Get your first advisory!\n\n"
        f"— ROPIAS | KCA University"
    )
    return send_message(phone, body)


def handle_incoming(from_number: str, body: str, db=None, User=None,
                    FarmFeedback=None) -> str:
    """
    Processes an incoming WhatsApp reply from a farmer.
    Called by the /webhook/whatsapp route.
    Returns the reply text to send back via TwiML.
    """
    from datetime import datetime
    cmd = body.strip().upper()

    # ── Find the farmer by phone number ──────────────────────────────────────
    farmer = None
    if User and db:
        clean = from_number.replace("whatsapp:", "").strip()
        farmer = User.query.filter_by(phone=clean, role="farmer").first()

    # ── Handle commands ───────────────────────────────────────────────────────
    if cmd == "STOP":
        if farmer and db:
            farmer.whatsapp_alerts = False
            db.session.commit()
        return (
            "You have been unsubscribed from ROPIAS WhatsApp alerts. "
            "Reply START anytime to resubscribe. Your farm data is preserved."
        )

    elif cmd == "START":
        if farmer and db:
            farmer.whatsapp_alerts = True
            db.session.commit()
        return (
            "Welcome back! You are resubscribed to ROPIAS daily alerts. "
            "Next advisory arrives tomorrow at 6:00 AM."
        )

    elif cmd == "STATUS":
        if farmer:
            return (
                f"Processing advisory for {farmer.full_name}... "
                f"You will receive your current farm status in a few moments."
            )
        return "Please register your farm coordinates to use STATUS."

    elif "NO RAIN" in cmd:
        if farmer and db and FarmFeedback:
            feedback = FarmFeedback(
                user_id       = farmer.id,
                latitude      = farmer.farm_latitude,
                longitude     = farmer.farm_longitude,
                feedback_type = "no_rain",
                notes         = body
            )
            db.session.add(feedback)
            db.session.commit()
        return (
            "Thank you for your report — it did not rain at your location. "
            "This helps us improve predictions for your region. 🙏"
        )

    else:
        return (
            "ROPIAS Commands:\n"
            "• STATUS — current farm advisory\n"
            "• NO RAIN — report no rainfall today\n"
            "• STOP — unsubscribe\n"
            "• START — resubscribe"
        )
