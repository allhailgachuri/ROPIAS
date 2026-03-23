"""
test_irrigation_engine.py
==========================
Unit tests for the soil moisture irrigation advisory engine.

Run with:
    pytest tests/ -v

Author: ROPIAS Project
"""

import pandas as pd
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from irrigation_engine import (
    classify_soil_moisture,
    compute_moisture_trend,
    IrrigationStatus
)


def make_soil_series(values: list, start: str = "2022-03-01") -> pd.Series:
    dates = pd.date_range(start=start, periods=len(values), freq="D")
    return pd.Series(values, index=dates, dtype=float)


class TestMoistureTrend:
    def test_rising_trend(self):
        soil = make_soil_series([0.30, 0.33, 0.36, 0.39, 0.42])
        assert compute_moisture_trend(soil) == "rising"

    def test_falling_trend(self):
        soil = make_soil_series([0.55, 0.51, 0.47, 0.43, 0.39])
        assert compute_moisture_trend(soil) == "falling"

    def test_stable_trend(self):
        soil = make_soil_series([0.50, 0.51, 0.50, 0.51, 0.50])
        assert compute_moisture_trend(soil) == "stable"


class TestIrrigationClassification:
    def test_irrigate_when_moisture_critically_low(self):
        soil = make_soil_series([0.25, 0.24, 0.23, 0.22, 0.21])
        result = classify_soil_moisture(soil)
        assert result["status"] == IrrigationStatus.IRRIGATE

    def test_optimal_when_moisture_in_range(self):
        soil = make_soil_series([0.45, 0.46, 0.45, 0.46, 0.45])
        result = classify_soil_moisture(soil)
        assert result["status"] == IrrigationStatus.OPTIMAL

    def test_saturated_when_moisture_too_high(self):
        soil = make_soil_series([0.80, 0.82, 0.85, 0.83, 0.81])
        result = classify_soil_moisture(soil)
        assert result["status"] == IrrigationStatus.SATURATED

    def test_no_data_when_all_nan(self):
        soil = make_soil_series([float('nan')] * 5)
        result = classify_soil_moisture(soil)
        assert result["status"] == IrrigationStatus.NO_DATA

    def test_boundary_exactly_at_threshold(self):
        """0.30 exactly should be OPTIMAL not IRRIGATE."""
        soil = make_soil_series([0.30, 0.30, 0.30, 0.30, 0.30])
        result = classify_soil_moisture(soil)
        assert result["status"] == IrrigationStatus.OPTIMAL

    def test_result_contains_gauge_data(self):
        soil = make_soil_series([0.45, 0.46, 0.45, 0.46, 0.45])
        result = classify_soil_moisture(soil)
        assert "gauge_data" in result
        assert "value" in result["gauge_data"]
        assert "critical_threshold" in result["gauge_data"]

    def test_moisture_percent_is_correct(self):
        """0.55 fraction should return 55.0%"""
        soil = make_soil_series([0.55] * 5)
        result = classify_soil_moisture(soil)
        assert result["moisture_percent"] == 55.0