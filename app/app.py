"""
app.py
=======
Flask web application for ROPIAS.
Serves the farmer dashboard and orchestrates the full data pipeline.

Run with:
    python app.py

Then open: http://localhost:5000

Author: ROPIAS Project
"""

import sys
import os

# ── Path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from flask import Flask, render_template, request, jsonify
from data_fetcher import fetch_climate_data, validate_kenya_coordinates
from onset_engine import classify_onset, OnsetResult
from irrigation_engine import classify_soil_moisture, IrrigationStatus

app = Flask(__name__)


# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def index():
    """Renders the main farmer dashboard."""
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    """
    Main analysis endpoint.

    Accepts JSON: { "latitude": float, "longitude": float }
    Returns JSON with onset classification, irrigation advisory,
    and chart data.
    """
    # ── Parse input ───────────────────────────────────────────────────────────
    try:
        body = request.get_json()
        lat = float(body.get("latitude"))
        lon = float(body.get("longitude"))
    except (TypeError, ValueError):
        return jsonify({
            "error": "Invalid coordinates. Please enter valid decimal numbers."
        }), 400

    # ── Validate coordinates ──────────────────────────────────────────────────
    if not validate_kenya_coordinates(lat, lon):
        return jsonify({
            "error": (
                "Coordinates are outside Kenya's bounds. "
                "Latitude must be between -5 and 5. "
                "Longitude must be between 34 and 42."
            )
        }), 400

    # ── Fetch NASA data ───────────────────────────────────────────────────────
    try:
        climate = fetch_climate_data(
            latitude=lat,
            longitude=lon,
            days_back=60
        )
    except ConnectionError as e:
        return jsonify({"error": str(e)}), 503
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    rain = climate["precipitation"]
    soil = climate["soil_moisture"]

    # ── Run engines ───────────────────────────────────────────────────────────
    onset      = classify_onset(rain)
    irrigation = classify_soil_moisture(soil)

    # ── Prepare chart data (last 14 days) ─────────────────────────────────────
    rain_14      = rain.tail(14)
    chart_labels = [d.strftime("%b %d") for d in rain_14.index]
    chart_values = [round(float(v), 2) for v in rain_14.values]

    # Soil moisture history for trend line (last 14 days)
    soil_14       = soil.tail(14)
    soil_values   = [
        round(float(v) * 100, 1) if not str(v) == 'nan' else None
        for v in soil_14.values
    ]

    # ── Build response ────────────────────────────────────────────────────────
    return jsonify({
        "onset": {
            "result":         onset["result"].value,
            "color":          onset["color"],
            "onset_date":     onset["onset_date"],
            "cumulative_rain": onset["cumulative_rain"],
            "summary":        onset["summary"]
        },
        "irrigation": {
            "status":             irrigation["status"].value,
            "moisture_percent":   irrigation["moisture_percent"],
            "moisture_category":  irrigation["moisture_category"],
            "trend":              irrigation["trend"],
            "color":              irrigation["color"],
            "summary":            irrigation["summary"],
            "gauge_data":         irrigation["gauge_data"]
        },
        "chart": {
            "labels":         chart_labels,
            "rainfall":       chart_values,
            "soil_moisture":  soil_values
        },
        "meta": {
            "latitude":   lat,
            "longitude":  lon,
            "start_date": climate["start_date"],
            "end_date":   climate["end_date"]
        }
    })


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint for deployment monitoring."""
    return jsonify({"status": "ok", "service": "ROPIAS"}), 200


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)