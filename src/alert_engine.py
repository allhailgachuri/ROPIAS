"""
alert_engine.py
===============
Background scheduler using APScheduler to run the analysis engine every 24 hours
for all subscribed users and send SMS alerts via Africa's Talking.
"""

import os
import africastalking
from apscheduler.schedulers.background import BackgroundScheduler
from database.db import db, AlertSubscription
from src.data_fetcher import fetch_climate_data
from src.onset_engine import classify_onset
from src.irrigation_engine import classify_soil_moisture

ALERT_MESSAGES = {
    "red": (
        "ROPIAS ALERT: Mvua ya udanganyifu imeonekana. "
        "FALSE ONSET detected at your farm. "
        "DO NOT plant. Dry spell expected."
    ),
    "green": (
        "ROPIAS ALERT: Mvua halisi imeanza. "
        "TRUE ONSET confirmed. "
        "SAFE TO PLANT this week. "
        "Soil moisture is optimal."
    ),
    "irrigate": (
        "ROPIAS ALERT: Udongo mkavu. "
        "Soil moisture critically low at your farm. "
        "IRRIGATE TODAY to protect your crops."
    )
}

def send_sms_alert(phone: str, message: str):
    """Wrapper to send SMS using Africa's Talking."""
    try:
        africastalking.initialize(
            username=os.getenv("AT_USERNAME", "sandbox"),
            api_key=os.getenv("AT_API_KEY", "dummy")
        )
        sms = africastalking.SMS
        # Need to format phone if it doesn't have country code, but assume frontend handles it.
        sms.send(message, [phone])
    except Exception as e:
        print(f"Failed to send SMS to {phone}: {e}")

def run_daily_alerts(app):
    """Runs the alert check for all subscriptions."""
    with app.app_context():
        print("Running daily ROPIAS alerts...")
        subs = AlertSubscription.query.filter_by(active=True).all()
        for sub in subs:
            try:
                climate = fetch_climate_data(sub.latitude, sub.longitude)
                onset = classify_onset(climate)
                irr = classify_soil_moisture(climate)
                
                # Check Onset Change
                if onset["color"] in ["red", "green"]:
                    send_sms_alert(sub.phone, ALERT_MESSAGES.get(onset["color"], ""))
                
                # Check Irrigation
                if irr.get("status") in ["Irrigate Immediately", "Irrigate Today"]:
                    send_sms_alert(sub.phone, ALERT_MESSAGES["irrigate"])
                    
            except Exception as e:
                print(f"Error processing alerts for {sub.phone}: {e}")

def start_scheduler(app):
    """Boots the APScheduler and attaches it to Flask app lifecycle."""
    scheduler = BackgroundScheduler(timezone="Africa/Nairobi")
    
    # Schedule to run every day at 6:00 AM East African Time
    scheduler.add_job(lambda: run_daily_alerts(app), 'cron', hour=6, minute=0)
    scheduler.start()
    print("ROPIAS Alert Scheduler started.")
    return scheduler
