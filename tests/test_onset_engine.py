"""
test_onset_engine.py
=====================
Unit tests for the rainfall onset detection engine.
Uses synthetic data to verify correct classification under
known conditions.

Run with:
    pytest tests/ -v

Author: ROPIAS Project
"""

import pandas as pd
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from onset_engine import (
    classify_onset,
    detect_dry_spell,
    find_onset_candidates,
    OnsetResult
)


# ── Helper ────────────────────────────────────────────────────────────────────
def make_series(values: list, start: str = "2022-03-01") -> pd.Series:
    """Creates a pandas Series with a DatetimeIndex from a list of values."""
    dates = pd.date_range(start=start, periods=len(values), freq="D")
    return pd.Series(values, index=dates, dtype=float)


# ══════════════════════════════════════════════════════════════════════════════
class TestDrySpellDetection:
    """Tests for the detect_dry_spell function."""

    def test_detects_exactly_7_consecutive_dry_days(self):
        """7 consecutive days below 1mm = dry spell."""
        rain = make_series([5, 5, 0, 0, 0, 0, 0, 0, 0, 5])
        assert detect_dry_spell(rain) is True

    def test_detects_long_dry_spell(self):
        """14 consecutive dry days should be detected."""
        rain = make_series([10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5])
        assert detect_dry_spell(rain) is True

    def test_6_dry_days_is_not_a_dry_spell(self):
        """6 consecutive dry days is below the 7-day threshold."""
        rain = make_series([5, 0, 0, 0, 0, 0, 0, 5])
        # Only 6 dry days between the rain events
        assert detect_dry_spell(rain) is False

    def test_rain_on_day_7_breaks_dry_spell(self):
        """Rain appearing on day 7 of a dry stretch should break the spell."""
        rain = make_series([5, 0, 0, 0, 0, 0, 0, 2, 5])
        assert detect_dry_spell(rain) is False

    def test_all_rainy_no_dry_spell(self):
        """Consistent daily rain should never trigger a dry spell."""
        rain = make_series([3, 2, 4, 5, 2, 3, 1.5, 2, 4, 3] * 3)
        assert detect_dry_spell(rain) is False

    def test_all_zeros_is_dry_spell(self):
        """All zeros should immediately trigger a dry spell."""
        rain = make_series([0] * 10)
        assert detect_dry_spell(rain) is True

    def test_nan_values_counted_as_dry(self):
        """NaN (missing data) should count as a dry day."""
        import math
        rain = make_series([5, float('nan')] * 5)
        # Every other day is NaN — need 7 consecutive to trigger
        # This alternating pattern should NOT trigger
        assert detect_dry_spell(rain) is False


# ══════════════════════════════════════════════════════════════════════════════
class TestOnsetCandidates:
    """Tests for the find_onset_candidates function."""

    def test_finds_candidates_above_threshold(self):
        """Days where rolling 2-day sum >= 20mm should be flagged."""
        rain = make_series([0, 0, 12, 10, 0, 0])
        # Day 3+4: 12+10 = 22mm → candidate
        candidates = find_onset_candidates(rain)
        assert candidates.any()

    def test_no_candidates_when_rain_too_light(self):
        """Light rain that never cumulates to 20mm should give no candidates."""
        rain = make_series([1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5])
        candidates = find_onset_candidates(rain)
        assert not candidates.any()


# ══════════════════════════════════════════════════════════════════════════════
class TestOnsetClassification:
    """Tests for the main classify_onset function."""

    def test_true_onset_detected(self):
        """
        Scenario: 30mm over 2 days, then 30 days of steady rain.
        Expected: True Onset.
        """
        values = (
            [0] * 10 +              # 10 quiet days
            [15, 16] +              # 31mm onset event (above 20mm threshold)
            [3, 2, 4, 2, 3, 2, 1.5, 2, 3, 4,   # steady drizzle
             2, 3, 1.5, 2, 3, 2, 4, 2, 3, 1.5,
             2, 3, 2, 4, 2, 3, 2, 4, 2, 3]      # 30 days, no dry spell
        )
        series = make_series(values)
        result = classify_onset(series)
        assert result["result"] == OnsetResult.TRUE_ONSET

    def test_false_onset_detected(self):
        """
        Scenario: 30mm over 2 days, then 8-day dry spell.
        Expected: False Onset.
        """
        values = (
            [0] * 10 +              # 10 quiet days
            [15, 16] +              # 31mm onset event
            [0] * 8 +               # 8-day dry spell
            [3, 2, 4, 2, 3, 2, 4, 2, 3, 2, 4, 2]  # rain returns
        )
        series = make_series(values)
        result = classify_onset(series)
        assert result["result"] == OnsetResult.FALSE_ONSET

    def test_no_onset_when_rain_always_too_low(self):
        """
        Scenario: 1.5mm every day — never reaches 20mm threshold.
        Expected: No Onset.
        """
        values = [1.5] * 45
        series = make_series(values)
        result = classify_onset(series)
        assert result["result"] == OnsetResult.NO_ONSET

    def test_insufficient_data_when_series_too_short(self):
        """
        Scenario: Only 10 days of data (need at least 32).
        Expected: Insufficient Data.
        """
        values = [5] * 10
        series = make_series(values)
        result = classify_onset(series)
        assert result["result"] == OnsetResult.INSUFFICIENT_DATA

    def test_result_includes_summary_text(self):
        """Every result must include a non-empty summary string."""
        values = [1.5] * 45
        series = make_series(values)
        result = classify_onset(series)
        assert isinstance(result["summary"], str)
        assert len(result["summary"]) > 0

    def test_result_includes_color(self):
        """Every result must include a color key for the frontend."""
        values = [1.5] * 45
        series = make_series(values)
        result = classify_onset(series)
        assert result["color"] in ("green", "red", "grey", "yellow")