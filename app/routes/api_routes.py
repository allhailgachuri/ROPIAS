"""
api_routes.py
==============
API endpoints for data analysis, historical queries, and third-party webhooks.
Includes the Twilio WhatsApp incoming webhook.
"""

from flask import Blueprint, request, jsonify
from flask_login import current_user
import sys, os

# DB and Models
from database.models import db, QueryLog, User, FarmFeedback, APICache

# Engines and Utilities
from src.data_fetcher import fetch_climate_data, validate_kenya_coordinates
from src.onset_engine import classify_onset
from src.irrigation_engine import classify_soil_moisture
from src.location_utils import get_coordinates_from_city
from src.forecast_engine import compute_planting_risk_score
from src.historical_engine import analyze_historical_season
from src.crop_registry import get_crops_by_category

api_bp = Blueprint("api", __name__)


@api_bp.route("/analyze", methods=["POST"])
def analyze():
    body = request.get_json()
    crop_key = body.get("crop", "maize")
    
    # Check if city or coords provided
    city = body.get("city")
    if city:
        lat, lon, address = get_coordinates_from_city(city)
        if lat is None:
            return jsonify({"error": "City not found. Please try entering precise coordinates."}), 400
    else:
        try:
            lat = float(body.get("latitude"))
            lon = float(body.get("longitude"))
            address = f"{lat}, {lon}"
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid coordinates."}), 400

    if not validate_kenya_coordinates(lat, lon):
        return jsonify({"error": "Coordinates are outside Kenya bounds."}), 400

    try:
        # Fetch data up to today
        climate = fetch_climate_data(latitude=lat, longitude=lon, days_back=60, include_forecast=False)
        # Fetch forecast explicitly for next 7 days
        forecast = fetch_climate_data(latitude=lat, longitude=lon, days_back=0, include_forecast=True)
    except ConnectionError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    # Extract 7-day forecast arrays
    rain_forecast = forecast["precipitation"].tail(7).values.tolist() if len(forecast["precipitation"]) >= 7 else []

    onset = classify_onset(climate, crop_key=crop_key)
    irrigation = classify_soil_moisture(climate, rain_forecast, crop_key=crop_key)

    # Save to QueryLog
    try:
        new_query = QueryLog(
            user_id = current_user.id if current_user.is_authenticated else None,
            latitude=lat, 
            longitude=lon,
            crop_key=crop_key,
            onset_result=onset.get("result", "None"),
            onset_color=onset.get("color", "grey"),
            moisture_pct=irrigation.get("moisture_percent", 0.0),
            irrigation_status=irrigation.get("status", "Unknown"),
            data_start=climate["start_date"],
            data_end=climate["end_date"]
        )
        db.session.add(new_query)
        db.session.commit()
    except Exception as e:
        print("Failed to save query to DB:", e)
        db.session.rollback()

    # Chart prep
    rain_14 = climate["precipitation"].tail(14)
    soil_14 = climate["soil_moisture"].tail(14)
    
    return jsonify({
        "location": {"latitude": lat, "longitude": lon, "address": address},
        "onset": onset,
        "irrigation": irrigation,
        "chart": {
            "labels": [d.strftime("%b %d") for d in rain_14.index],
            "rainfall": [round(float(v), 2) for v in rain_14.values],
            "soil_moisture": [round(float(v)*100, 1) if str(v) != 'nan' else None for v in soil_14.values]
        }
    })


@api_bp.route("/api/crops", methods=["GET"])
def api_crops():
    return jsonify({"categories": get_crops_by_category()})


@api_bp.route("/api/forecast", methods=["POST"])
def api_forecast():
    body = request.get_json()
    lat = float(body.get("latitude"))
    lon = float(body.get("longitude"))
    
    climate = fetch_climate_data(lat, lon, days_back=5, include_forecast=True)
    f_rain = climate["precipitation"].tail(7).values.tolist()
    f_et = climate["evapotranspiration"].tail(7).values.tolist()
    
    soil_series = climate["soil_moisture"].dropna()
    c_soil = float(soil_series.iloc[-1]) if len(soil_series) > 0 else 0.3
    
    risk = compute_planting_risk_score(f_rain, f_et, c_soil)
    return jsonify({"forecast_risk": risk})


@api_bp.route("/api/historical", methods=["GET"])
def api_historical():
    lat = float(request.args.get("lat"))
    lon = float(request.args.get("lon"))
    year = int(request.args.get("year"))
    season = request.args.get("season", "long_rains")
    
    res = analyze_historical_season(lat, lon, year, season)
    return jsonify({"historical": res})


@api_bp.route("/webhook/whatsapp", methods=["POST"])
def whatsapp_webhook():
    """
    Twilio calls this URL when a farmer sends a WhatsApp reply.
    Must be publicly accessible.
    Local dev: use ngrok → ngrok http 5000
    Set in Twilio Console → Messaging → Sandbox Settings →
      'When a message comes in': https://YOUR-URL/webhook/whatsapp
    """
    from twilio.twiml.messaging_response import MessagingResponse
    from src.whatsapp_alerts import handle_incoming
    
    from_number = request.form.get("From", "")
    body        = request.form.get("Body", "")

    reply_text = handle_incoming(from_number, body, db, User, FarmFeedback)

    resp = MessagingResponse()
    resp.message(reply_text)
    return str(resp), 200, {"Content-Type": "text/xml"}


@api_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "ROPIAS ML Edition - Phase 2"}), 200
