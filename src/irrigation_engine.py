"""
irrigation_engine.py
====================
Analyzes root zone soil moisture (GWETROOT) and produces
an ET-adjusted irrigation advisory.
"""

import pandas as pd
from enum import Enum

class IrrigationStatus(Enum):
    CRITICAL_IMMEDIATE = "Irrigate Immediately"
    HIGH_TODAY = "Irrigate Today"
    MEDIUM_SOON = "Irrigate Within 2 Days"
    WATCH_TOMORROW = "Monitor — Irrigate Tomorrow"
    OPTIMAL = "No Action Needed"
    SATURATED = "Do Not Irrigate"
    NO_DATA = "Soil Moisture Data Unavailable"

def compute_days_until_critical(current_gwetroot: float, et_rate: float, rain_forecast: list) -> int:
    """Estimates days until soil moisture hits 0.30 threshold."""
    moisture = current_gwetroot
    critical = 0.30
    if not rain_forecast:
        rain_forecast = [0.0]*7
        
    for day, forecast_rain in enumerate(rain_forecast):
        # 1mm rain ≈ 0.01 increase in GWETROOT. Evaporation loss ET * 0.005
        moisture += (forecast_rain * 0.01) - (et_rate * 0.005)
        moisture = max(0.0, min(1.0, moisture))
        
        if moisture < critical:
            return day + 1  # Days until critical
            
    return None

def classify_soil_moisture(climate: dict, rain_forecast: list = None) -> dict:
    soil_series = climate.get("soil_moisture", pd.Series(dtype=float))
    et_series = climate.get("evapotranspiration", pd.Series(dtype=float))
    
    clean_soil = soil_series.dropna()
    clean_et = et_series.dropna()
    
    if len(clean_soil) == 0:
        return {
            "status": IrrigationStatus.NO_DATA.value,
            "current_value": None,
            "moisture_percent": None,
            "moisture_category": "Unknown",
            "trend": "stable",
            "color": "grey",
            "summary": "Soil moisture data is unavailable for this location.",
            "gauge_data": {"value": 0, "min": 0, "max": 100, "critical_threshold": 30, "saturation_threshold": 70}
        }
        
    current = float(clean_soil.iloc[-1])
    et_rate = float(clean_et.iloc[-1]) if len(clean_et) > 0 else 3.0
    
    moisture_percent = round(current * 100, 1)
    
    # 5-day trend
    trend = "stable"
    if len(clean_soil) >= 5:
        slope = float(clean_soil.iloc[-1]) - float(clean_soil.iloc[-5])
        if slope > 0.03: trend = "rising"
        elif slope < -0.03: trend = "falling"
        
    days_to_critical = compute_days_until_critical(current, et_rate, rain_forecast)

    if current < 0.20:
        status = IrrigationStatus.CRITICAL_IMMEDIATE
        category = "Critical"
        color = "red"
        summary = "CRITICAL. Soil is completely dry. Irrigate immediately to save crops."
    elif 0.20 <= current < 0.30:
        if et_rate > 4.0:
            status = IrrigationStatus.HIGH_TODAY
            category = "Dry"
            color = "orange"
            summary = "HIGH RISK. Fast drying detected. Irrigate today."
        else:
            status = IrrigationStatus.MEDIUM_SOON
            category = "Dry"
            color = "yellow"
            summary = "MEDIUM RISK. Soil is dry but drying slowly. Irrigate within 2 days."
    elif 0.30 <= current <= 0.40 and et_rate > 5.0 and trend == "falling":
        status = IrrigationStatus.WATCH_TOMORROW
        category = "Watch"
        color = "yellow"
        summary = "WATCH. Soil is currently okay but falling fast due to high heat. Irrigate tomorrow."
    elif current > 0.70:
        status = IrrigationStatus.SATURATED
        category = "Saturated"
        color = "blue"
        summary = "DO NOT IRRIGATE. Soil is saturated, risk of root rot."
    else:
        status = IrrigationStatus.OPTIMAL
        category = "Optimal"
        color = "green"
        summary = "OPTIMAL. Soil moisture is within the healthy range."
        
    return {
        "status": status.value,
        "current_value": round(current, 4),
        "moisture_percent": moisture_percent,
        "moisture_category": category,
        "trend": trend,
        "color": color,
        "summary": summary,
        "days_to_critical": days_to_critical,
        "gauge_data": {
            "value": moisture_percent,
            "min": 0, "max": 100,
            "critical_threshold": 30,
            "saturation_threshold": 70
        }
    }