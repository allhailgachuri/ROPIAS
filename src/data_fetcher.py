"""
data_fetcher.py
================
Handles all communication with the NASA POWER API.
Fetches daily precipitation (PRECTOTCORR) and root zone
soil wetness (GWETROOT) for a given GPS coordinate and date range.

Author: ROPIAS Project
"""

import requests
import pandas as pd
from datetime import datetime, timedelta


# ── Constants ────────────────────────────────────────────────────────────────
NASA_BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
MISSING_VALUE = -999.0
DEFAULT_DAYS_BACK = 60

# Kenya bounding box for input validation
KENYA_LAT_MIN, KENYA_LAT_MAX = -5.0, 5.0
KENYA_LON_MIN, KENYA_LON_MAX = 34.0, 42.0


# ── Helpers ───────────────────────────────────────────────────────────────────
def get_date_range(days_back: int = DEFAULT_DAYS_BACK) -> tuple:
    """Returns (start_date, end_date) strings in YYYYMMDD format."""
    end_date = datetime.today()
    start_date = end_date - timedelta(days=days_back)
    return start_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d")


def validate_kenya_coordinates(latitude: float, longitude: float) -> bool:
    """
    Validates that coordinates fall within Kenya's bounding box.
    Latitude:  -5 to 5
    Longitude: 34 to 42
    """
    return (
        KENYA_LAT_MIN <= latitude <= KENYA_LAT_MAX and
        KENYA_LON_MIN <= longitude <= KENYA_LON_MAX
    )


def parse_nasa_series(raw_dict: dict, fill_missing_with=0.0) -> pd.Series:
    """
    Converts a raw NASA POWER parameter dict into a clean pandas Series
    with a proper DatetimeIndex. Replaces -999.0 sentinel values.

    Args:
        raw_dict: dict of {YYYYMMDD: float} from NASA API response
        fill_missing_with: value to replace -999.0 (use float('nan') for soil)

    Returns:
        Clean pandas Series indexed by date
    """
    series = pd.Series(raw_dict)
    series.index = pd.to_datetime(series.index, format="%Y%m%d")
    series = series.replace(MISSING_VALUE, fill_missing_with)
    return series.sort_index()


# ── Main fetch function ───────────────────────────────────────────────────────
def fetch_climate_data(
    latitude: float,
    longitude: float,
    start_date: str = None,
    end_date: str = None,
    days_back: int = DEFAULT_DAYS_BACK
) -> dict:
    """
    Fetches PRECTOTCORR and GWETROOT from NASA POWER API.

    Args:
        latitude:   Farm GPS latitude  (e.g. 0.28 for Kakamega)
        longitude:  Farm GPS longitude (e.g. 34.75 for Kakamega)
        start_date: Optional override. Format: "YYYYMMDD"
        end_date:   Optional override. Format: "YYYYMMDD"
        days_back:  Days of history to fetch when dates are not specified

    Returns:
        dict:
            precipitation  → pd.Series (daily rainfall in mm)
            soil_moisture  → pd.Series (GWETROOT fraction 0–1)
            latitude       → float
            longitude      → float
            start_date     → str
            end_date       → str

    Raises:
        ValueError:      If coordinates are outside Kenya bounds
        ConnectionError: If NASA API times out or returns an error
    """
    if not validate_kenya_coordinates(latitude, longitude):
        raise ValueError(
            f"Coordinates ({latitude}, {longitude}) are outside Kenya. "
            f"Latitude must be {KENYA_LAT_MIN}–{KENYA_LAT_MAX}, "
            f"Longitude must be {KENYA_LON_MIN}–{KENYA_LON_MAX}."
        )

    if start_date is None or end_date is None:
        start_date, end_date = get_date_range(days_back)

    params = {
        "parameters": "PRECTOTCORR,GWETROOT",
        "community": "AG",
        "longitude": longitude,
        "latitude": latitude,
        "start": start_date,
        "end": end_date,
        "format": "JSON"
    }

    try:
        response = requests.get(NASA_BASE_URL, params=params, timeout=15)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise ConnectionError(
            "NASA POWER API timed out after 15 seconds. "
            "Check your internet connection and try again."
        )
    except requests.exceptions.HTTPError as e:
        raise ConnectionError(f"NASA POWER API returned an error: {e}")
    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            "Could not reach NASA POWER API. "
            "Check your internet connection."
        )

    try:
        raw = response.json()
        parameters = raw["properties"]["parameter"]
    except (KeyError, ValueError) as e:
        raise ConnectionError(
            f"Unexpected response format from NASA API: {e}"
        )

    precipitation = parse_nasa_series(
        parameters["PRECTOTCORR"],
        fill_missing_with=0.0       # Assume 0mm for missing rain days
    )
    soil_moisture = parse_nasa_series(
        parameters["GWETROOT"],
        fill_missing_with=float('nan')  # NaN for missing soil — 0 is misleading
    )

    return {
        "precipitation": precipitation,
        "soil_moisture": soil_moisture,
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date
    }