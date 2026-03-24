"""
data_fetcher.py
================
Handles communication with the NASA POWER API.
Fetches historical and forecast data with caching to prevent rate limits.

Includes parameters:
- PRECTOTCORR: Precipitation
- GWETROOT: Root Zone Soil Wetness
- GWETTOP: Surface Soil Wetness
- EVPTRNS: Evapotranspiration
- T2M_MAX: Max Temp
- T2M_MIN: Min Temp
- WS2M: Wind Speed
- RH2M: Relative Humidity
"""

import requests
import pandas as pd
import json
from datetime import datetime, timedelta

NASA_BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
MISSING_VALUE = -999.0
DEFAULT_DAYS_BACK = 60
DEFAULT_FORECAST_DAYS = 7

# Kenya bounding box
KENYA_LAT_MIN, KENYA_LAT_MAX = -5.0, 5.0
KENYA_LON_MIN, KENYA_LON_MAX = 34.0, 42.0

PARAMETERS = "PRECTOTCORR,GWETROOT,GWETTOP,EVPTRNS,T2M_MAX,T2M_MIN,WS2M,RH2M"

def get_date_range(days_back: int = DEFAULT_DAYS_BACK, forecast_days: int = 0) -> tuple:
    end_date = datetime.today() + timedelta(days=forecast_days)
    start_date = datetime.today() - timedelta(days=days_back)
    return start_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d")

def validate_kenya_coordinates(latitude: float, longitude: float) -> bool:
    return (
        KENYA_LAT_MIN <= latitude <= KENYA_LAT_MAX and
        KENYA_LON_MIN <= longitude <= KENYA_LON_MAX
    )

def parse_nasa_series(raw_dict: dict, fill_missing_with=0.0) -> pd.Series:
    series = pd.Series(raw_dict)
    series.index = pd.to_datetime(series.index, format="%Y%m%d")
    series = series.replace(MISSING_VALUE, fill_missing_with)
    
    # Forward fill gaps < 3 days (interpolation as requested)
    series = series.interpolate(method='linear', limit=2)
    return series.sort_index()

def fetch_climate_data(latitude: float, longitude: float, start_date: str = None, end_date: str = None, days_back: int = DEFAULT_DAYS_BACK, include_forecast: bool = False) -> dict:
    if not validate_kenya_coordinates(latitude, longitude):
        raise ValueError(f"Coordinates outside Kenya limits.")

    forecast_days = DEFAULT_FORECAST_DAYS if include_forecast else 0
    if start_date is None or end_date is None:
        start_date, end_date = get_date_range(days_back, forecast_days)

    cache_key = f"{latitude}_{longitude}_{start_date}_{end_date}_{PARAMETERS}"
    
    # Try Cache
    try:
        from flask import current_app
        from database.db import db, ApiCache
        if current_app:
            cached = ApiCache.query.filter_by(cache_key=cache_key).first()
            if cached and cached.expires_at > datetime.utcnow():
                return _parse_response(json.loads(cached.payload), latitude, longitude, start_date, end_date)
    except Exception as e:
        print("Cache miss or error:", e)

    params = {
        "parameters": PARAMETERS,
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
        raw = response.json()
    except Exception as e:
        raise ConnectionError(f"NASA POWER API error: {e}")

    try:
        from flask import current_app
        from database.db import db, ApiCache
        if current_app:
            new_cache = ApiCache(
                cache_key=cache_key,
                expires_at=datetime.utcnow() + timedelta(hours=24), # Cache for a day
                payload=json.dumps(raw)
            )
            db.session.add(new_cache)
            db.session.commit()
    except Exception:
        pass

    return _parse_response(raw, latitude, longitude, start_date, end_date)

def _parse_response(raw: dict, lat, lon, start_date, end_date) -> dict:
    parameters = raw["properties"]["parameter"]
    
    res = {
        "precipitation": parse_nasa_series(parameters.get("PRECTOTCORR", {}), 0.0),
        "soil_moisture": parse_nasa_series(parameters.get("GWETROOT", {}), float('nan')),
        "surface_soil": parse_nasa_series(parameters.get("GWETTOP", {}), float('nan')),
        "evapotranspiration": parse_nasa_series(parameters.get("EVPTRNS", {}), float('nan')),
        "temp_max": parse_nasa_series(parameters.get("T2M_MAX", {}), float('nan')),
        "temp_min": parse_nasa_series(parameters.get("T2M_MIN", {}), float('nan')),
        "wind_speed": parse_nasa_series(parameters.get("WS2M", {}), float('nan')),
        "humidity": parse_nasa_series(parameters.get("RH2M", {}), float('nan')),
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date
    }
    return res