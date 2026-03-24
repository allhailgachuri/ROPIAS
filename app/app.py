"""
app.py
=======
Flask web application for ROPIAS.
Serves the farmer dashboard and orchestrates the full data pipeline.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

from src.data_fetcher import fetch_climate_data, validate_kenya_coordinates
from src.onset_engine import classify_onset
from src.irrigation_engine import classify_soil_moisture
from src.location_utils import get_coordinates_from_city
from src.forecast_engine import compute_planting_risk_score
from src.historical_engine import analyze_historical_season
from src.crop_registry import get_crops_by_category

# DB and Alerts
from database.db import db, AlertSubscription, Query, ApiCache, HistoricalOnset
from src.alert_engine import start_scheduler

app = Flask(__name__)
CORS(app)

# ── Configuration ─────────────────────────────────────────────────────────────
basedir = os.path.abspath(os.path.dirname(__file__))

# Workaround for SQLite C-library path encoding bug with emojis
safe_db_dir = os.path.expanduser('~/.ropias/database')
os.makedirs(safe_db_dir, exist_ok=True)
db_path = os.path.join(safe_db_dir, 'ropias.db').replace('\\', '/')

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()
    # Start scheduler only if not running in a reloader thread to avoid duplicates
    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        start_scheduler(app)


# ── Frontend Routes ───────────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/officer", methods=["GET"])
def officer():
    return render_template("officer.html")

@app.route("/historical", methods=["GET"])
def historical():
    return render_template("historical.html")

@app.route("/api/docs", methods=["GET"])
def api_docs():
    return render_template("api_docs.html")


# ── API Routes ────────────────────────────────────────────────────────────────
@app.route("/analyze", methods=["POST"])
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

    # Save Query to DB
    try:
        new_query = Query(
            latitude=lat, longitude=lon,
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


@app.route("/api/crops", methods=["GET"])
def api_crops():
    return jsonify({"categories": get_crops_by_category()})


@app.route("/api/forecast", methods=["POST"])
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


@app.route("/api/historical", methods=["GET"])
def api_historical():
    lat = float(request.args.get("lat"))
    lon = float(request.args.get("lon"))
    year = int(request.args.get("year"))
    season = request.args.get("season", "long_rains")
    
    res = analyze_historical_season(lat, lon, year, season)
    return jsonify({"historical": res})


@app.route("/api/alerts/subscribe", methods=["POST"])
def subscribe_alert():
    body = request.get_json()
    phone = body.get("phone")
    lat = float(body.get("latitude"))
    lon = float(body.get("longitude"))
    
    # Ensure standard international format
    if not phone.startswith('+'):
        phone = '+' + phone
        
    sub = AlertSubscription.query.filter_by(phone=phone).first()
    if sub:
        sub.latitude = lat
        sub.longitude = lon
        sub.active = True
    else:
        sub = AlertSubscription(phone=phone, latitude=lat, longitude=lon)
        db.session.add(sub)
    db.session.commit()
    return jsonify({"status": "success", "message": f"Subscribed {phone} successfully."})


@app.route("/api/alerts/unsubscribe", methods=["DELETE"])
def unsubscribe_alert():
    body = request.get_json()
    phone = body.get("phone")
    if not phone.startswith('+'): phone = '+' + phone
        
    sub = AlertSubscription.query.filter_by(phone=phone).first()
    if sub:
        sub.active = False
        db.session.commit()
        return jsonify({"status": "unsubscribed"})
    return jsonify({"error": "Not registered."}), 404


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "ROPIAS ML Edition"}), 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)