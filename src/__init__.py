"""
ROPIAS — Rainfall Onset Prediction & Irrigation Advisory System
src package init
"""
from .data_fetcher import fetch_climate_data, validate_kenya_coordinates
from .onset_engine import classify_onset, OnsetResult
from .irrigation_engine import classify_soil_moisture, IrrigationStatus

__all__ = [
    "fetch_climate_data",
    "validate_kenya_coordinates",
    "classify_onset",
    "OnsetResult",
    "classify_soil_moisture",
    "IrrigationStatus"
]