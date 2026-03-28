"""
onset_engine.py
================
Implements True/False onset detection logic with ML enhancements.
Refactored to accept dynamic crop thresholds spanning all Kenya crops.
"""

import pandas as pd
from enum import Enum
from src.ml_model import build_features, predict_onset_ml
from src.crop_registry import get_crop_thresholds, get_crop

class OnsetResult(Enum):
    TRUE_ONSET = "True Onset"
    FALSE_ONSET = "False Onset"
    NO_ONSET = "No Onset Detected"
    INSUFFICIENT_DATA = "Insufficient Data"
    UNCERTAIN = "UNCERTAIN"


def compute_rule_confidence(cumulative_rain: float, threshold: float,
                             dry_spell_found: bool, validation_days_checked: int) -> int:
    """
    Deterministic confidence score (45–95%) based on agronomic rule inputs.
    Used when ML model is not available or as a fallback baseline.
    """
    base = min(cumulative_rain / threshold, 1.5) * 60           # 0–90 pts
    validation_bonus = (validation_days_checked / 30) * 10       # 0–10 pts
    dry_spell_penalty = -25 if dry_spell_found else 0
    confidence = round(min(95, max(45, base + validation_bonus + dry_spell_penalty)))
    return confidence


# Global Constants that aren't crop specific
DRY_SPELL_THRESHOLD_MM = 1.0 # agronomic source: rainfall intensity under 1mm mostly lost to evaporation
VALIDATION_WINDOW_DAYS = 30  # agronomic source: early vegetative stage monitoring window

def detect_dry_spell(rain_series: pd.Series, threshold_mm: float, consecutive_days: int) -> bool:
    """Scans forward to identify false onsets triggered by sudden dry spells."""
    consecutive = 0
    for value in rain_series:
        if pd.isna(value) or float(value) < threshold_mm:
            consecutive += 1
            if consecutive >= consecutive_days:
                return True
        else:
            consecutive = 0
    return False

def compute_rolling_sum(rain_series: pd.Series, window: int) -> pd.Series:
    """Computes the accumulation of water over the planting window."""
    return rain_series.rolling(window=window, min_periods=1).sum()

def find_onset_candidates(rain_series: pd.Series, threshold_mm: float, window_days: int) -> pd.Series:
    """Finds exact dates where the accumulation breached the crop's unique threshold."""
    rolling_sum = compute_rolling_sum(rain_series, window_days)
    return rolling_sum >= threshold_mm

def classify_onset(climate: dict, crop_key: str = "maize") -> dict:
    """
    Main entrypoint. Evaluates the climate arrays against the exact
    agronomic rules for the user's selected crop.
    """
    rain_series = climate.get("precipitation", pd.Series(dtype=float))
    
    # Grab the specific threshold parameters for this crop
    crop_data = get_crop(crop_key)
    thresholds = get_crop_thresholds(crop_key)
    
    ONSET_THRESHOLD_MM = thresholds["onset_threshold_mm"]
    ONSET_WINDOW_DAYS = thresholds["onset_window_days"]
    DRY_SPELL_CONSECUTIVE_DAYS = thresholds["dry_spell_days"]
    
    min_data_required = ONSET_WINDOW_DAYS + VALIDATION_WINDOW_DAYS
    display_name = crop_data["display_name"]
    
    if len(rain_series) < min_data_required:
        return {
            "result": OnsetResult.INSUFFICIENT_DATA.value,
            "color": "none", 
            "summary": f"Not enough data to run onset checks for {display_name}. At least {min_data_required} days required.",
            "ml_metadata": None,
            "chart_data": {}
        }

    candidates_mask = find_onset_candidates(rain_series, ONSET_THRESHOLD_MM, ONSET_WINDOW_DAYS)
    candidate_dates = rain_series[candidates_mask].index

    if len(candidate_dates) == 0:
        return {
            "result": OnsetResult.NO_ONSET.value,
            "color": "none",
            "summary": f"No rainfall event has exceeded the {ONSET_THRESHOLD_MM}mm threshold required for {display_name}.",
            "ml_metadata": None,
            "chart_data": {"rolling_sum": compute_rolling_sum(rain_series, ONSET_WINDOW_DAYS).tolist()}
        }

    for onset_date in reversed(candidate_dates):
        window_start = onset_date - pd.Timedelta(days=ONSET_WINDOW_DAYS - 1)
        onset_window = rain_series[(rain_series.index >= window_start) & (rain_series.index <= onset_date)]
        cumulative = float(onset_window.sum())

        validation_end = onset_date + pd.Timedelta(days=VALIDATION_WINDOW_DAYS)
        validation_window = rain_series[(rain_series.index > onset_date) & (rain_series.index <= validation_end)]

        dry_spell = detect_dry_spell(validation_window, DRY_SPELL_THRESHOLD_MM, DRY_SPELL_CONSECUTIVE_DAYS)
        rule_based_result = "False Onset" if dry_spell else "True Onset"
        
        # Build ML features and predict
        features = build_features(rain_series, climate, onset_date)
        ml_eval = predict_onset_ml(features, rule_based_result)
        
        classification = ml_eval["classification"]
        confidence = ml_eval["confidence"]

        # Formulate output based on final classification
        if classification == "False Onset":
            color = "false"
            summary = f"WARNING — FALSE ONSET (Confidence: {confidence*100:.0f}%). A {round(cumulative, 1)}mm event occurred but a devastating {DRY_SPELL_CONSECUTIVE_DAYS}-day dry spell threatens {display_name} germination. DO NOT plant."
        elif classification == "True Onset":
            color = "true"
            summary = f"TRUE ONSET (Confidence: {confidence*100:.0f}%). Rains confirmed with {round(cumulative, 1)}mm over {ONSET_WINDOW_DAYS} days. Suitable for {display_name}. SAFE TO PLANT."
        else:
            color = "uncertain"
            summary = f"UNCERTAIN CONDITIONS (Confidence: {confidence*100:.0f}%). Rule engine and ML disagree around {display_name} tolerance. Wait 3 more days."

        return {
            "result": classification,
            "onset_date": onset_date.strftime("%B %d, %Y"),
            "cumulative_rain": round(cumulative, 2),
            "color": color,
            "summary": summary,
            "ml_metadata": ml_eval,
            "crop": crop_data,
            "chart_data": {"rolling_sum": compute_rolling_sum(rain_series, ONSET_WINDOW_DAYS).tolist()}
        }

    return {
        "result": OnsetResult.NO_ONSET.value,
        "color": "none",
        "summary": "No conclusive onset detected.",
        "ml_metadata": None,
        "crop": crop_data,
        "chart_data": {"rolling_sum": compute_rolling_sum(rain_series, ONSET_WINDOW_DAYS).tolist()}
    }