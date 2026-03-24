"""
forecast_engine.py
==================
Computes a 0–100 planting risk score for each of the next 7 days.
Leverages NASA POWER API's forecast endpoint values.
"""

def compute_planting_risk_score(forecast_rain: list, forecast_et: list, current_soil: float) -> dict:
    """
    Computes planting risk (0-100) for the next 7 days based on extrapolated soil moisture.
    
    Args:
        forecast_rain: list of 7 daily rain predictions (mm)
        forecast_et: list of 7 daily evapotranspiration predictions (mm)
        current_soil: current GWETROOT fraction (0-1)
    """
    scores = []
    
    # Handle missing or NaN current soil by assuming a dry baseline if entirely unknown.
    if str(current_soil) == 'nan' or current_soil is None:
        moisture = 0.20
    else:
        moisture = float(current_soil)
    
    # Pad to 7 days if incomplete
    if not forecast_rain or len(forecast_rain) < 7:
        try:
            forecast_rain = list(forecast_rain) + [0.0] * (7 - len(forecast_rain))
        except TypeError:
            forecast_rain = [0.0]*7
    if not forecast_et or len(forecast_et) < 7:
        forecast_et = list(forecast_et) + [3.0] * (7 - len(forecast_et))  # Default 3mm ET
        
    for i in range(7):
        try:
            rain = float(forecast_rain[i]) if str(forecast_rain[i]) != 'nan' else 0.0
            et = float(forecast_et[i]) if str(forecast_et[i]) != 'nan' else 3.0
        except:
            rain, et = 0.0, 3.0
            
        # Update projected moisture
        moisture += (rain * 0.01) - (et * 0.005)
        moisture  = max(0.0, min(1.0, moisture))
        
        # Risk factors
        moisture_risk = max(0, (0.30 - moisture) / 0.30) * 50  # 0–50 pts
        dry_day_risk  = 30 if rain < 1.0 else 0                 # 0–30 pts
        et_risk       = min(20, et * 2)                         # 0–20 pts
        
        total = min(100.0, moisture_risk + dry_day_risk + et_risk)
        scores.append(round(total, 1))
    
    max_score = max(scores) if scores else 0
    safe_days = [i+1 for i, s in enumerate(scores) if s < 30]
    
    return {
        "daily_risk_scores": scores,
        "peak_risk_day": scores.index(max_score) + 1 if scores else 1,
        "overall_risk": "High" if max_score > 70 else "Medium" if max_score > 40 else "Low",
        "safe_planting_days": safe_days
    }
