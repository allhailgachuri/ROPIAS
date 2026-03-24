"""
ml_model.py
===========
Machine Learning classification layer for Rainfall Onsets.
"""

import os
import joblib
import pandas as pd

# We look for a trained model in the ml/models directory
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'ml', 'models', 'logistic_regression.pkl')

def build_features(rain_series: pd.Series, climate: dict, candidate_date: pd.Timestamp) -> dict:
    """Builds the feature vector for a specific onset candidate date."""
    
    # Rainfall
    window_2day = rain_series.loc[:candidate_date].tail(2)
    window_7day = rain_series.loc[:candidate_date].tail(7)
    window_30day = rain_series.loc[:candidate_date].tail(30)
    window_14day = rain_series.loc[:candidate_date].tail(14)
    
    rain_2day_sum = window_2day.sum()
    rain_7day_sum = window_7day.sum()
    rain_30day_sum = window_30day.sum()
    rain_intensity = window_7day.max() if not window_7day.empty else 0.0
    rain_days_count = (window_14day > 1.0).sum()
    
    # Soil
    gwetroot = climate.get("soil_moisture", pd.Series())
    gwetroot_sub = gwetroot.loc[:candidate_date].dropna()
    current_soil = float(gwetroot_sub.iloc[-1]) if len(gwetroot_sub) > 0 else 0.3
    
    soil_7day_delta = 0.0
    if len(gwetroot_sub) >= 7:
        soil_7day_delta = float(gwetroot_sub.iloc[-1]) - float(gwetroot_sub.iloc[-7])
        
    trend = "stable"
    if soil_7day_delta > 0.03: trend = "rising"
    elif soil_7day_delta < -0.03: trend = "falling"
    
    # Atmosphere
    evp = climate.get("evapotranspiration", pd.Series()).loc[:candidate_date].dropna()
    evapotranspiration = float(evp.iloc[-1]) if len(evp) > 0 else 3.0
    
    tmax = climate.get("temp_max", pd.Series()).loc[:candidate_date].dropna()
    temp_max = float(tmax.iloc[-1]) if len(tmax) > 0 else 25.0
    
    rh = climate.get("humidity", pd.Series()).loc[:candidate_date].dropna()
    humidity = float(rh.iloc[-1]) if len(rh) > 0 else 60.0
    
    return {
        "rain_2day_sum": float(rain_2day_sum),
        "rain_7day_sum": float(rain_7day_sum),
        "rain_30day_sum": float(rain_30day_sum),
        "rain_intensity": float(rain_intensity),
        "rain_days_count": int(rain_days_count),
        "gwetroot_current": float(current_soil),
        "gwetroot_7day_delta": float(soil_7day_delta),
        "gwetroot_trend": trend,
        "evapotranspiration": float(evapotranspiration),
        "temp_max": float(temp_max),
        "humidity": float(humidity),
        "day_of_year": candidate_date.dayofyear,
        "month": candidate_date.month,
        "is_long_rains_period": candidate_date.month in [3, 4, 5],
        "is_short_rains_period": candidate_date.month in [10, 11, 12]
    }

def predict_onset_ml(features: dict, rule_based_result: str) -> dict:
    """Runs the extracted features through the trained model."""
    
    ml_result = rule_based_result
    confidence = 0.85 # Default mock confidence

    # To convert categorical to numeric for model
    trend_map = {"rising": 1, "stable": 0, "falling": -1}
    
    # If the model exists, use it. Otherwise, return mock data.
    if os.path.exists(MODEL_PATH):
        try:
            model = joblib.load(MODEL_PATH)
            
            # Prepare df
            df = pd.DataFrame([features])
            df["gwetroot_trend"] = df["gwetroot_trend"].map(trend_map)
            df = df.astype(float)
            
            prob = model.predict_proba(df)[0]
            # Assume class 1 is True Onset
            is_true = prob[1] > 0.5
            ml_result = "True Onset" if is_true else "False Onset"
            confidence = round(max(prob), 2)
            
        except Exception as e:
            print(f"ML Model Error: {e}")
            pass
    else:
        # Construct mock probability based on intuitive physics
        if rule_based_result == "True Onset":
            if features["is_long_rains_period"] and features["rain_30day_sum"] > 50:
                confidence = 0.92
            else:
                confidence = 0.75
                # Sometimes mock a disagreement to show UNCERTAIN
                if features["temp_max"] > 30 and features["evapotranspiration"] > 5:
                    ml_result = "False Onset"
                    confidence = 0.60
        else:
            if features["gwetroot_7day_delta"] < 0:
                confidence = 0.88
            else:
                confidence = 0.70

    agreement = (ml_result == rule_based_result)
    
    return {
        "rule_based_result": rule_based_result,
        "ml_result": ml_result,
        "confidence": confidence,
        "agreement": agreement,
        "classification": rule_based_result if agreement else "UNCERTAIN"
    }
