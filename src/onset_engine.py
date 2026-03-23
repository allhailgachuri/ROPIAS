"""
onset_engine.py
================
Implements the True/False rainfall onset detection logic.

Scientific basis:
  - Mugalavai et al. (2008): onset = cumulative >= 20mm within 1–2 days,
    no dry spell (7+ consecutive days < 1mm) in the following 30 days.
  - Nkunzimana et al. (2021): 20mm within 3 consecutive days, same dry
    spell rule.
  - Kipkorir et al. (2007): 40mm within 4 days; validation period 30 days.

This engine uses the Mugalavai/Nkunzimana consensus (20mm / 2-day / 7-day
dry spell) as it is the most widely cited for Western Kenya smallholder
farming contexts.

Author: ROPIAS Project
"""

import pandas as pd
from enum import Enum


# ── Result enum ───────────────────────────────────────────────────────────────
class OnsetResult(Enum):
    TRUE_ONSET          = "True Onset"
    FALSE_ONSET         = "False Onset"
    NO_ONSET            = "No Onset Detected"
    INSUFFICIENT_DATA   = "Insufficient Data"


# ── Scientific thresholds (literature-derived) ────────────────────────────────
RAINFALL_THRESHOLD_MM       = 20.0   # Cumulative rain to qualify as onset candidate
ONSET_WINDOW_DAYS           = 2      # Days over which to accumulate rainfall
DRY_SPELL_THRESHOLD_MM      = 1.0    # Daily rain below this = dry day
DRY_SPELL_CONSECUTIVE_DAYS  = 7      # Consecutive dry days = dry spell
VALIDATION_WINDOW_DAYS      = 30     # Days ahead to check for dry spells
MIN_DATA_REQUIRED           = ONSET_WINDOW_DAYS + VALIDATION_WINDOW_DAYS


# ── Core logic functions ──────────────────────────────────────────────────────
def detect_dry_spell(
    rain_series: pd.Series,
    threshold_mm: float = DRY_SPELL_THRESHOLD_MM,
    consecutive_days: int = DRY_SPELL_CONSECUTIVE_DAYS
) -> bool:
    """
    Checks if a qualifying dry spell exists anywhere in the given series.

    A dry spell = `consecutive_days` or more days where daily rainfall
    is below `threshold_mm`.

    Args:
        rain_series:      pandas Series of daily rainfall values
        threshold_mm:     Rain below this counts as a dry day (default 1.0mm)
        consecutive_days: How many consecutive dry days = a dry spell (default 7)

    Returns:
        True if a dry spell is found, False otherwise
    """
    consecutive = 0
    for value in rain_series:
        if pd.isna(value) or float(value) < threshold_mm:
            consecutive += 1
            if consecutive >= consecutive_days:
                return True
        else:
            consecutive = 0
    return False


def find_onset_candidates(
    rain_series: pd.Series,
    threshold_mm: float = RAINFALL_THRESHOLD_MM,
    window_days: int = ONSET_WINDOW_DAYS
) -> pd.Series:
    """
    Finds all candidate onset dates: dates where the rolling cumulative
    rainfall over `window_days` meets or exceeds `threshold_mm`.

    Args:
        rain_series:  Daily rainfall Series indexed by date
        threshold_mm: Minimum cumulative rainfall to qualify (default 20mm)
        window_days:  Rolling window size in days (default 2)

    Returns:
        Boolean Series — True at each candidate onset date
    """
    rolling_sum = rain_series.rolling(
        window=window_days,
        min_periods=1
    ).sum()
    return rolling_sum >= threshold_mm


def compute_rolling_sum(rain_series: pd.Series,
                        window: int = ONSET_WINDOW_DAYS) -> pd.Series:
    """Returns the rolling cumulative rainfall series for charting."""
    return rain_series.rolling(window=window, min_periods=1).sum()


# ── Main classification function ──────────────────────────────────────────────
def classify_onset(rain_series: pd.Series) -> dict:
    """
    Main entry point. Analyzes a rainfall time series and returns the
    onset classification with full metadata.

    Args:
        rain_series: pandas Series indexed by date, daily rainfall in mm.
                     Should contain at least 32 days of data.

    Returns:
        dict with keys:
          result          → OnsetResult enum value
          onset_date      → str (human-readable) or None
          cumulative_rain → float (mm) or None
          dry_spell_found → bool or None
          color           → str ('green', 'red', 'grey', 'yellow')
          summary         → str (plain-language advisory for farmers)
          chart_data      → dict with rolling sums for visualization
    """
    # ── Guard: not enough data ────────────────────────────────────────────────
    if len(rain_series) < MIN_DATA_REQUIRED:
        return {
            "result": OnsetResult.INSUFFICIENT_DATA,
            "onset_date": None,
            "cumulative_rain": None,
            "dry_spell_found": None,
            "color": "yellow",
            "summary": (
                "Not enough data to classify. At least 32 days of data "
                "is required. Data Insufficient — do NOT use for planting decisions."
            ),
            "chart_data": {}
        }

    # ── Find candidate onset dates ────────────────────────────────────────────
    candidates_mask = find_onset_candidates(rain_series)
    candidate_dates = rain_series[candidates_mask].index

    # ── Guard: no rain event meets the threshold ──────────────────────────────
    if len(candidate_dates) == 0:
        return {
            "result": OnsetResult.NO_ONSET,
            "onset_date": None,
            "cumulative_rain": 0.0,
            "dry_spell_found": False,
            "color": "grey",
            "summary": (
                "No rainfall event has exceeded the 20mm threshold in "
                "the current data window. The rains have not yet started "
                "in this region. Do NOT plant yet."
            ),
            "chart_data": {
                "rolling_sum": compute_rolling_sum(rain_series).tolist()
            }
        }

    # ── Evaluate each candidate (most recent first) ───────────────────────────
    for onset_date in reversed(candidate_dates):

        # Cumulative rain at this candidate date
        window_start = onset_date - pd.Timedelta(days=ONSET_WINDOW_DAYS - 1)
        onset_window = rain_series[
            (rain_series.index >= window_start) &
            (rain_series.index <= onset_date)
        ]
        cumulative = float(onset_window.sum())

        # Validation window: next 30 days after onset
        validation_end = onset_date + pd.Timedelta(days=VALIDATION_WINDOW_DAYS)
        validation_window = rain_series[
            (rain_series.index > onset_date) &
            (rain_series.index <= validation_end)
        ]

        # Check for dry spell
        dry_spell = detect_dry_spell(validation_window)

        if dry_spell:
            return {
                "result": OnsetResult.FALSE_ONSET,
                "onset_date": onset_date.strftime("%B %d, %Y"),
                "cumulative_rain": round(cumulative, 2),
                "dry_spell_found": True,
                "color": "red",
                "summary": (
                    f"WARNING — FALSE ONSET DETECTED. "
                    f"A rainfall event of {round(cumulative, 1)}mm was recorded "
                    f"around {onset_date.strftime('%B %d')}. However, a dry spell "
                    f"of 7 or more consecutive days was detected in the following "
                    f"30 days. Seeds planted now are at HIGH RISK of failure. "
                    f"Do NOT plant yet. Wait for a confirmed sustained rain period."
                ),
                "chart_data": {
                    "rolling_sum": compute_rolling_sum(rain_series).tolist()
                }
            }
        else:
            return {
                "result": OnsetResult.TRUE_ONSET,
                "onset_date": onset_date.strftime("%B %d, %Y"),
                "cumulative_rain": round(cumulative, 2),
                "dry_spell_found": False,
                "color": "green",
                "summary": (
                    f"TRUE ONSET CONFIRMED — SAFE TO PLANT. "
                    f"{round(cumulative, 1)}mm of rainfall was recorded around "
                    f"{onset_date.strftime('%B %d')}, with no dry spell detected "
                    f"in the following 30-day window. Soil conditions are "
                    f"supportive for planting. Proceed with planting."
                ),
                "chart_data": {
                    "rolling_sum": compute_rolling_sum(rain_series).tolist()
                }
            }

    # ── Fallback (should rarely reach here) ──────────────────────────────────
    return {
        "result": OnsetResult.NO_ONSET,
        "onset_date": None,
        "cumulative_rain": 0.0,
        "dry_spell_found": False,
        "color": "grey",
        "summary": "No conclusive onset detected in the current data window.",
        "chart_data": {}
    }