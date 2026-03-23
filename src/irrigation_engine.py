"""
irrigation_engine.py
=====================
Analyzes root zone soil moisture (GWETROOT) and produces
an irrigation advisory for smallholder farmers.

GWETROOT scale (NASA POWER):
  0.0  – 0.29  →  Dry       (irrigate urgently)
  0.30 – 0.70  →  Optimal   (no irrigation needed)
  0.71 – 1.0   →  Saturated (do not irrigate — risk of root rot)

Critical threshold of 0.30 is derived from:
  Omondi & Mutua (2025): Validation of NASA POWER soil moisture
  parameters for precision agriculture in semi-arid Kenya.

Author: ROPIAS Project
"""

import pandas as pd
from enum import Enum


# ── Result enum ───────────────────────────────────────────────────────────────
class IrrigationStatus(Enum):
    IRRIGATE    = "Irrigate Today"
    OPTIMAL     = "Soil Moisture Optimal"
    SATURATED   = "Do Not Irrigate — Soil Saturated"
    NO_DATA     = "Soil Moisture Data Unavailable"


# ── Thresholds ────────────────────────────────────────────────────────────────
CRITICAL_MOISTURE_THRESHOLD = 0.30   # Below this → crops at risk
SATURATION_THRESHOLD        = 0.70   # Above this → waterlogging risk
TREND_WINDOW_DAYS           = 5      # Days to compute moisture trend


# ── Helper: moisture trend ────────────────────────────────────────────────────
def compute_moisture_trend(soil_series: pd.Series,
                           window: int = TREND_WINDOW_DAYS) -> str:
    """
    Computes whether soil moisture is rising, falling, or stable
    over the last `window` days.

    Returns: 'rising', 'falling', or 'stable'
    """
    clean = soil_series.dropna()
    if len(clean) < window:
        return "stable"

    recent = clean.tail(window)
    slope = recent.iloc[-1] - recent.iloc[0]

    if slope > 0.03:
        return "rising"
    elif slope < -0.03:
        return "falling"
    else:
        return "stable"


# ── Main classification function ──────────────────────────────────────────────
def classify_soil_moisture(soil_series: pd.Series) -> dict:
    """
    Analyzes soil moisture data and returns a full irrigation advisory.

    Args:
        soil_series: pandas Series indexed by date, GWETROOT values (0.0–1.0)

    Returns:
        dict with keys:
          status              → IrrigationStatus enum value
          current_value       → float (latest GWETROOT reading)
          moisture_percent    → float (value as 0–100%)
          moisture_category   → str ('Dry', 'Optimal', 'Saturated', 'Unknown')
          trend               → str ('rising', 'falling', 'stable')
          color               → str ('blue_alert', 'blue_ok', 'blue_warn', 'grey')
          summary             → str (plain-language advisory)
          gauge_data          → dict for frontend gauge chart
    """
    clean = soil_series.dropna()

    # ── Guard: no data ────────────────────────────────────────────────────────
    if len(clean) == 0:
        return {
            "status": IrrigationStatus.NO_DATA,
            "current_value": None,
            "moisture_percent": None,
            "moisture_category": "Unknown",
            "trend": "stable",
            "color": "grey",
            "summary": (
                "Soil moisture data is unavailable for this location. "
                "The NASA API may not have recent data for these coordinates. "
                "Please try again later or check a nearby location."
            ),
            "gauge_data": {
                "value": 0,
                "min": 0,
                "max": 100,
                "critical_threshold": 30,
                "saturation_threshold": 70
            }
        }

    current = float(clean.iloc[-1])
    moisture_percent = round(current * 100, 1)
    trend = compute_moisture_trend(clean)

    # ── Classify ──────────────────────────────────────────────────────────────
    if current < CRITICAL_MOISTURE_THRESHOLD:
        status = IrrigationStatus.IRRIGATE
        category = "Dry"
        color = "blue_alert"

        trend_note = ""
        if trend == "falling":
            trend_note = " Moisture is actively dropping — irrigate urgently."
        elif trend == "rising":
            trend_note = " Moisture is recovering slightly, but still below safe levels."

        summary = (
            f"IRRIGATE TODAY. Root zone soil moisture is critically low "
            f"at {moisture_percent}% (threshold: 30%). "
            f"Plants are at risk of water stress and crop failure."
            f"{trend_note}"
        )

    elif current >= SATURATION_THRESHOLD:
        status = IrrigationStatus.SATURATED
        category = "Saturated"
        color = "blue_warn"
        summary = (
            f"DO NOT IRRIGATE. Root zone soil moisture is at {moisture_percent}% "
            f"— soil is saturated. Additional water may cause root rot, "
            f"anaerobic conditions, and fungal disease. "
            f"Allow the soil to drain naturally before irrigating."
        )

    else:
        status = IrrigationStatus.OPTIMAL
        category = "Optimal"
        color = "blue_ok"

        trend_note = ""
        if trend == "falling":
            trend_note = (
                f" Moisture is declining — monitor closely. "
                f"Consider irrigating if it drops below 30%."
            )

        summary = (
            f"SOIL MOISTURE OPTIMAL. Root zone moisture is at "
            f"{moisture_percent}% — within the healthy range (30%–70%). "
            f"No irrigation needed today.{trend_note}"
        )

    return {
        "status": status,
        "current_value": round(current, 4),
        "moisture_percent": moisture_percent,
        "moisture_category": category,
        "trend": trend,
        "color": color,
        "summary": summary,
        "gauge_data": {
            "value": moisture_percent,
            "min": 0,
            "max": 100,
            "critical_threshold": CRITICAL_MOISTURE_THRESHOLD * 100,
            "saturation_threshold": SATURATION_THRESHOLD * 100
        }
    }