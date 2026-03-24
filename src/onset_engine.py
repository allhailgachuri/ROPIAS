"""
onset_engine.py
================
Implements True/False onset detection logic with ML enhancements.
"""

import pandas as pd
from enum import Enum
from ml_model import build_features, predict_onset_ml

class OnsetResult(Enum):
    TRUE_ONSET = "True Onset"
    FALSE_ONSET = "False Onset"
    NO_ONSET = "No Onset Detected"
    INSUFFICIENT_DATA = "Insufficient Data"
    UNCERTAIN = "UNCERTAIN"

# Thresholds
RAINFALL_THRESHOLD_MM = 20.0
ONSET_WINDOW_DAYS = 2
DRY_SPELL_THRESHOLD_MM = 1.0
DRY_SPELL_CONSECUTIVE_DAYS = 7
VALIDATION_WINDOW_DAYS = 30
MIN_DATA_REQUIRED = ONSET_WINDOW_DAYS + VALIDATION_WINDOW_DAYS

def detect_dry_spell(rain_series: pd.Series, threshold_mm=DRY_SPELL_THRESHOLD_MM, consecutive_days=DRY_SPELL_CONSECUTIVE_DAYS) -> bool:
    consecutive = 0
    for value in rain_series:
        if pd.isna(value) or float(value) < threshold_mm:
            consecutive += 1
            if consecutive >= consecutive_days:
                return True
        else:
            consecutive = 0
    return False

def compute_rolling_sum(rain_series: pd.Series, window=ONSET_WINDOW_DAYS) -> pd.Series:
    return rain_series.rolling(window=window, min_periods=1).sum()

def find_onset_candidates(rain_series: pd.Series, threshold_mm=RAINFALL_THRESHOLD_MM, window_days=ONSET_WINDOW_DAYS) -> pd.Series:
    rolling_sum = compute_rolling_sum(rain_series, window_days)
    return rolling_sum >= threshold_mm

def classify_onset(climate: dict) -> dict:
    rain_series = climate.get("precipitation", pd.Series(dtype=float))
    
    if len(rain_series) < MIN_DATA_REQUIRED:
        return {
            "result": OnsetResult.INSUFFICIENT_DATA.value,
            "color": "yellow",
            "summary": "Not enough data. At least 32 days required.",
            "ml_metadata": None,
            "chart_data": {}
        }

    candidates_mask = find_onset_candidates(rain_series)
    candidate_dates = rain_series[candidates_mask].index

    if len(candidate_dates) == 0:
        return {
            "result": OnsetResult.NO_ONSET.value,
            "color": "grey",
            "summary": "No rainfall event has exceeded the 20mm threshold in the data window.",
            "ml_metadata": None,
            "chart_data": {"rolling_sum": compute_rolling_sum(rain_series).tolist()}
        }

    for onset_date in reversed(candidate_dates):
        window_start = onset_date - pd.Timedelta(days=ONSET_WINDOW_DAYS - 1)
        onset_window = rain_series[(rain_series.index >= window_start) & (rain_series.index <= onset_date)]
        cumulative = float(onset_window.sum())

        validation_end = onset_date + pd.Timedelta(days=VALIDATION_WINDOW_DAYS)
        validation_window = rain_series[(rain_series.index > onset_date) & (rain_series.index <= validation_end)]

        dry_spell = detect_dry_spell(validation_window)
        rule_based_result = "False Onset" if dry_spell else "True Onset"
        
        # Build ML features and predict
        features = build_features(rain_series, climate, onset_date)
        ml_eval = predict_onset_ml(features, rule_based_result)
        
        classification = ml_eval["classification"]
        confidence = ml_eval["confidence"]

        # Formulate output based on final classification
        if classification == "False Onset":
            color = "red"
            summary = f"WARNING — FALSE ONSET (Confidence: {confidence*100:.0f}%). A {round(cumulative, 1)}mm event occurred but dry spell risk is severe. DO NOT plant."
        elif classification == "True Onset":
            color = "green"
            summary = f"TRUE ONSET (Confidence: {confidence*100:.0f}%). Rains confirmed with {round(cumulative, 1)}mm. SAFE TO PLANT."
        else:
            color = "orange"
            summary = f"UNCERTAIN CONDITIONS (Confidence: {confidence*100:.0f}%). Rule engine and ML model disagree. Wait 3 more days before planting."

        return {
            "result": classification,
            "onset_date": onset_date.strftime("%B %d, %Y"),
            "cumulative_rain": round(cumulative, 2),
            "color": color,
            "summary": summary,
            "ml_metadata": ml_eval,
            "chart_data": {"rolling_sum": compute_rolling_sum(rain_series).tolist()}
        }

    return {
        "result": OnsetResult.NO_ONSET.value,
        "color": "grey",
        "summary": "No conclusive onset detected.",
        "ml_metadata": None,
        "chart_data": {"rolling_sum": compute_rolling_sum(rain_series).tolist()}
    }