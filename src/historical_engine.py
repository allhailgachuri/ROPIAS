"""
historical_engine.py
====================
Runs the pipeline on a full historical season.
"""
from src.data_fetcher import fetch_climate_data
from src.onset_engine import classify_onset
from src.irrigation_engine import classify_soil_moisture

def count_dry_spells(rain_series):
    # Quick utility to count dry spells
    spells = 0
    consecutive = 0
    for val in rain_series:
        if val < 1.0:
            consecutive += 1
            if consecutive == 7:
                spells += 1
        else:
            consecutive = 0
    return spells

def analyze_historical_season(latitude: float, longitude: float, year: int, season: str) -> dict:
    season_ranges = {
        "long_rains": (f"{year}0201", f"{year}0630"),
        "short_rains": (f"{year}0901", f"{year}1231")
    }
    
    start, end = season_ranges.get(season, (f"{year}0101", f"{year}1231"))
    
    climate = fetch_climate_data(latitude, longitude, start_date=start, end_date=end, include_forecast=False)
    
    onset = classify_onset(climate)
    irrigation = classify_soil_moisture(climate)
    
    rain = climate["precipitation"]
    soil = climate["soil_moisture"]
    
    return {
        "year": year,
        "season": season,
        "onset_result": onset,
        "irrigation_result": irrigation,
        "total_seasonal_rain": float(rain.sum()),
        "dry_spell_count": count_dry_spells(rain),
        "days_below_critical_moisture": int((soil < 0.30).sum())
    }
