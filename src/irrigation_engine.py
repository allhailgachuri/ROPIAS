"""
irrigation_engine.py
====================
Analyzes root zone soil moisture (GWETROOT) against specific crop tolerances
to produce an ET-adjusted irrigation advisory.
"""

import pandas as pd
from enum import Enum
from src.crop_registry import get_crop, get_crop_thresholds

class IrrigationStatus(Enum):
    CRITICAL_IMMEDIATE = "Irrigate Immediately"
    HIGH_TODAY = "Irrigate Today"
    MEDIUM_SOON = "Irrigate Within 2 Days"
    WATCH_TOMORROW = "Monitor — Irrigate Tomorrow"
    OPTIMAL = "No Action Needed"
    SATURATED = "Do Not Irrigate"
    NO_DATA = "Soil Moisture Data Unavailable"

def compute_days_until_critical(current_gwetroot: float, et_rate: float, rain_forecast: list, critical_threshold: float) -> int:
    """Estimates days until soil moisture drops below the crop-specific critical threshold."""
    moisture = current_gwetroot
    if not rain_forecast:
        rain_forecast = [0.0]*7
        
    for day, forecast_rain in enumerate(rain_forecast):
        # 1mm rain ≈ 0.01 increase in GWETROOT. Evaporation loss ET * 0.005
        moisture += (forecast_rain * 0.01) - (et_rate * 0.005)
        moisture = max(0.0, min(1.0, moisture))
        
        if moisture < critical_threshold:
            return day + 1
            
    return None

def classify_soil_moisture(climate: dict, rain_forecast: list = None, crop_key: str = "maize") -> dict:
    """
    Main entrypoint. Evaluates the climate arrays against the exact
    agronomic moisture rules for the user's selected crop.
    """
    soil_series = climate.get("soil_moisture", pd.Series(dtype=float))
    et_series = climate.get("evapotranspiration", pd.Series(dtype=float))
    
    clean_soil = soil_series.dropna()
    clean_et = et_series.dropna()
    
    crop_data = get_crop(crop_key)
    thresholds = get_crop_thresholds(crop_key)
    
    CRITICAL = thresholds["critical_moisture"]
    OPT_MIN = thresholds["optimal_moisture_min"]
    OPT_MAX = thresholds["optimal_moisture_max"]
    display_name = crop_data["display_name"]
    
    if len(clean_soil) == 0:
        return {
            "status": IrrigationStatus.NO_DATA.value,
            "current_value": None,
            "moisture_percent": None,
            "moisture_category": "Unknown",
            "trend": "stable",
            "color": "none",
            "summary": "Soil moisture data is unavailable for this location.",
            "gauge_data": {"value": 0, "min": 0, "max": 100, "critical_threshold": int(CRITICAL*100), "saturation_threshold": int(OPT_MAX*100)}
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
        
    days_to_critical = compute_days_until_critical(current, et_rate, rain_forecast, CRITICAL)

    if current < CRITICAL:
        status = IrrigationStatus.CRITICAL_IMMEDIATE
        category = "Critical"
        color = "irrigate"
        summary = f"CRITICAL. Soil moisture is below the {CRITICAL*100}% threshold for {display_name}. Irrigate immediately to save crops."
    elif CRITICAL <= current < OPT_MIN:
        if et_rate > 4.0:
            status = IrrigationStatus.HIGH_TODAY
            category = "Dry"
            color = "irrigate"
            summary = f"HIGH RISK. Fast drying detected for {display_name}. Evapotranspiration is high. Irrigate today."
        else:
            status = IrrigationStatus.MEDIUM_SOON
            category = "Dry"
            color = "false"
            summary = f"MEDIUM RISK. {display_name} soil is dry but drying slowly. Irrigate within 2 days."
    elif OPT_MIN <= current <= OPT_MAX:
        status = IrrigationStatus.OPTIMAL
        category = "Optimal"
        color = "true"
        summary = f"OPTIMAL. Moisture is sitting beautifully between {OPT_MIN*100}% and {OPT_MAX*100}% for {display_name}."
    else: # > OPT_MAX
        status = IrrigationStatus.SATURATED
        category = "Saturated"
        color = "none" # Navy/Teal system treats saturated gently
        summary = f"DO NOT IRRIGATE. Heavy saturation detected for {display_name}, risk of suffocation."
        
    return {
        "status": status.value,
        "current_value": round(current, 4),
        "moisture_percent": moisture_percent,
        "moisture_category": category,
        "trend": trend,
        "color": color,
        "summary": summary,
        "days_to_critical": days_to_critical,
        "crop": crop_data,
        "gauge_data": {
            "value": moisture_percent,
            "min": 0, "max": 100,
            "critical_threshold": int(CRITICAL * 100),
            "opt_min_threshold": int(OPT_MIN * 100),
            "saturation_threshold": int(OPT_MAX * 100)
        }
    }