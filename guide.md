# 🌧️ ROPIAS — Complete Beginner's Expert Guide

### _Rainfall Onset Prediction & Irrigation Advisory System_

**A Data Science Project — From Zero to GitHub-Ready**

---

> **Who this guide is for:** You have a full-stack web dev background and QA experience,
> but you're new to data science. This guide treats you as an intelligent adult and walks
> you through every layer of this project — tools, theory, code, GitHub setup, and beyond.

---

## PART 0 — BIG PICTURE: WHAT ARE WE ACTUALLY BUILDING?

Before installing anything, understand the architecture in plain English:

```
[Farmer enters GPS coordinates]
         ↓
[Python fetches data from NASA POWER API]
         ↓
[Pandas processes 30 days of rainfall + soil moisture data]
         ↓
[Onset Engine: Is this rain real or a false alarm?]
[Irrigation Engine: Does the soil need water?]
         ↓
[Flask serves the result as a web page]
         ↓
[Bootstrap + Chart.js shows Green/Red/Blue advisory to farmer]
```

That's the entire system. Each section below builds one piece of that pipeline.

---

## PART 1 — TOOLS TO DOWNLOAD & INSTALL

### 1.1 Python 3.x (The Language)

Everything runs in Python. You need version 3.10 or higher.

- **Download:** https://www.python.org/downloads/
- **Docs:** https://docs.python.org/3/
- **Verify install:** Open terminal → type `python --version`

> **Beginner tip:** During installation on Windows, tick "Add Python to PATH" —
> this saves enormous frustration later.

---

### 1.2 VS Code (Code Editor)

This is where you'll write all your code.

- **Download:** https://code.visualstudio.com/
- **Docs:** https://code.visualstudio.com/docs
- **Extensions to install inside VS Code:**
  - `Python` (by Microsoft)
  - `Pylance`
  - `Jupyter` (for running notebooks)
  - `GitLens`

---

### 1.3 Git (Version Control)

You need this to push your project to GitHub.

- **Download:** https://git-scm.com/downloads
- **Docs:** https://git-scm.com/doc
- **Verify:** `git --version` in terminal

---

### 1.4 GitHub Account

Where your project will live publicly for collaborators.

- **Create account:** https://github.com
- **GitHub Docs:** https://docs.github.com/en

---

### 1.5 Jupyter Notebook / JupyterLab (Exploration & Prototyping)

This is how all data scientists explore data — interactive cells where you run code line by line and see results immediately. Think of it as a scientific scratchpad.

- **Install via pip:** `pip install jupyterlab`
- **Docs:** https://jupyter.org/documentation
- **Launch:** `jupyter lab` in your terminal

---

### 1.6 Anaconda (Optional but Recommended for Beginners)

Anaconda is a Python distribution that comes with everything pre-installed. It includes Jupyter, pandas, numpy, matplotlib — all in one installer. Recommended if you want to avoid dependency headaches.

- **Download:** https://www.anaconda.com/download
- **Docs:** https://docs.anaconda.com/

---

### 1.7 Postman (API Testing)

You'll use this to test the NASA POWER API manually before writing code — seeing the raw data in a visual interface first makes the code far easier to write.

- **Download:** https://www.postman.com/downloads/
- **Docs:** https://learning.postman.com/docs/

---

## PART 2 — PYTHON LIBRARIES (INSTALL VIA PIP)

Run these in your terminal one by one:

```bash
pip install pandas
pip install numpy
pip install requests
pip install flask
pip install matplotlib
pip install seaborn
pip install plotly
pip install pytest
pip install python-dotenv
```

### What each one does in THIS project:

| Library         | Role in ROPIAS                                                      | Documentation                           |
| --------------- | ------------------------------------------------------------------- | --------------------------------------- |
| `pandas`        | Reads NASA API data, processes 30-day rainfall arrays, rolling sums | https://pandas.pydata.org/docs/         |
| `numpy`         | Mathematical operations on arrays (thresholds, sums)                | https://numpy.org/doc/                  |
| `requests`      | Makes HTTP calls to NASA POWER API                                  | https://requests.readthedocs.io/        |
| `flask`         | Serves the web application                                          | https://flask.palletsprojects.com/      |
| `matplotlib`    | Generates charts for analysis & validation                          | https://matplotlib.org/stable/users/    |
| `seaborn`       | Statistical visualizations for EDA                                  | https://seaborn.pydata.org/             |
| `plotly`        | Interactive charts for deeper data exploration                      | https://plotly.com/python/              |
| `pytest`        | Testing your engine functions                                       | https://docs.pytest.org/en/stable/      |
| `python-dotenv` | Manages environment variables (API keys etc.)                       | https://pypi.org/project/python-dotenv/ |

---

## PART 3 — THE NASA POWER API (Your Data Source)

This is the single most important external resource in the project. NASA provides this completely free, no API key required for basic access.

### 3.1 API Documentation

- **Main docs:** https://power.larc.nasa.gov/docs/
- **API endpoint reference:** https://power.larc.nasa.gov/docs/services/api/
- **Parameter dictionary:** https://power.larc.nasa.gov/parameters/
- **Data Access Viewer (visual explorer):** https://power.larc.nasa.gov/data-access-viewer/

### 3.2 The Two Parameters You Need

**PRECTOTCORR** — Corrected Daily Total Precipitation

- Unit: mm/day
- What it means: How many millimeters of rain fell at a GPS point on a given day
- This is the primary input for the onset detection logic

**GWETROOT** — Root Zone Soil Wetness

- Unit: fraction (0.0 to 1.0, where 1.0 = fully saturated)
- What it means: How much water is available to plant roots (top 1 meter of soil)
- This drives the irrigation advisory

### 3.3 How to Call the API (Manually First)

Open your browser or Postman and paste this URL — it fetches 30 days of rainfall
for a location in Western Kenya (Kakamega area):

```
https://power.larc.nasa.gov/api/temporal/daily/point?parameters=PRECTOTCORR,GWETROOT&community=AG&longitude=34.75&latitude=0.28&start=20220301&end=20220430&format=JSON
```

You'll get a JSON response with a `properties.parameter` object containing
date-keyed values for both parameters. This is your raw data.

### 3.4 Understanding the Response

```json
{
  "properties": {
    "parameter": {
      "PRECTOTCORR": {
        "20220301": 0.0,
        "20220302": 12.4,
        "20220303": 8.1,
        ...
      },
      "GWETROOT": {
        "20220301": 0.42,
        "20220302": 0.51,
        ...
      }
    }
  }
}
```

Each key is a date in `YYYYMMDD` format. Each value is the measurement for that day.
NASA uses -999.0 as the "missing data" sentinel value — you'll need to handle this.

---

## PART 4 — DATA SCIENCE CONCEPTS YOU NEED TO UNDERSTAND

These are the concepts powering the system. Explained from scratch.

### 4.1 Rolling/Cumulative Sum

**What it is:** Adding up values over a sliding window of days.

**Why it matters:** You don't classify a rainfall event from a single day.
You look at what happened over 2–4 days combined.

```python
# Example: 4-day cumulative sum
import pandas as pd

rainfall = pd.Series([0, 5, 12, 8, 1, 0, 0])
cumsum_2day = rainfall.rolling(window=2).sum()
# This tells you: "In any 2-day window, how much rain fell total?"
```

**Documentation:** https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.rolling.html

---

### 4.2 Dry Spell Detection

**What it is:** Finding consecutive days where rainfall drops below 1mm.

**Why it matters:** After initial rain, if the soil dries out for 7+ consecutive
days, seeds planted during that initial rain will die. This is a "False Onset."

```python
def has_dry_spell(rain_series, threshold_mm=1.0, consecutive_days=7):
    """
    Returns True if a dry spell of `consecutive_days` exists in the series.
    """
    consecutive = 0
    for val in rain_series:
        if val < threshold_mm:
            consecutive += 1
            if consecutive >= consecutive_days:
                return True
        else:
            consecutive = 0
    return False
```

---

### 4.3 Threshold Classification

**What it is:** Comparing a value to a predefined cutoff to make a decision.

**Why it matters:** This is the core logic of both your engines.

```
Onset Engine:
  IF cumulative_2day_rain >= 20mm AND no dry spell in next 30 days:
      → True Onset (Green)
  IF cumulative_2day_rain >= 20mm BUT dry spell detected:
      → False Onset (Red)
  ELSE:
      → No Onset Detected (Grey)

Irrigation Engine:
  IF GWETROOT < 0.30:
      → Irrigate Today (Blue)
  ELSE:
      → Do Not Irrigate (Blue outline)
```

---

### 4.4 Time Series Data

**What it is:** Data that is indexed by time (date), where the sequence matters.

**Why it matters:** NASA POWER gives you time-series data. The order of days matters —
you can't shuffle rainfall records like you would with a regular dataset.

**Key pandas operations for time series:**

```python
# Convert date-keyed dict to pandas Series with DatetimeIndex
import pandas as pd

data = {"20220301": 5.0, "20220302": 12.0, "20220303": 3.0}
series = pd.Series(data)
series.index = pd.to_datetime(series.index, format="%Y%m%d")
```

**Documentation:** https://pandas.pydata.org/docs/user_guide/timeseries.html

---

### 4.5 Data Cleaning & Null Handling

**What it is:** Identifying and replacing bad/missing data before analysis.

**Why it matters:** NASA uses -999.0 for missing values. If you accidentally sum
-999 into your rainfall total, your classification will be completely wrong.

```python
# Replace NASA's missing value sentinel with NaN (pandas' null)
series = series.replace(-999.0, pd.NA)

# Then decide: fill with 0 (assume no rain) or drop the window
series = series.fillna(0)  # Conservative: assume 0mm for missing days
```

---

## PART 5 — PROJECT FILE STRUCTURE

Set up your GitHub repository with this exact structure from day one:

```
ropias/
│
├── README.md                    ← Project description, setup instructions
├── requirements.txt             ← All pip packages (auto-generated)
├── .gitignore                   ← Files Git should not track
├── .env.example                 ← Template for environment variables
│
├── data/                        ← Raw API data samples & historical CSVs
│   ├── sample_western_kenya.json
│   └── validation_2022_false_start.json
│
├── notebooks/                   ← Jupyter notebooks for exploration & EDA
│   ├── 01_nasa_api_exploration.ipynb
│   ├── 02_onset_logic_development.ipynb
│   └── 03_irrigation_logic_development.ipynb
│
├── src/                         ← Core Python engine modules
│   ├── __init__.py
│   ├── data_fetcher.py          ← NASA API calls
│   ├── onset_engine.py          ← True/False onset logic
│   ├── irrigation_engine.py     ← Soil moisture advisory logic
│   └── utils.py                 ← Shared helpers (date formatting, etc.)
│
├── tests/                       ← Unit tests for each engine
│   ├── test_data_fetcher.py
│   ├── test_onset_engine.py
│   └── test_irrigation_engine.py
│
├── app/                         ← Flask web application
│   ├── app.py                   ← Main Flask app
│   ├── templates/
│   │   └── index.html
│   └── static/
│       ├── css/
│       └── js/
│
└── docs/                        ← Academic documents
    ├── proposal.pdf
    └── srs.pdf
```

---

## PART 6 — STEP-BY-STEP BUILD GUIDE

### STEP 1: Set Up Your Environment

```bash
# 1. Create your project folder
mkdir ropias
cd ropias

# 2. Create a virtual environment (keeps your project's packages isolated)
python -m venv venv

# 3. Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install pandas numpy requests flask matplotlib pytest python-dotenv

# 5. Save your requirements
pip freeze > requirements.txt

# 6. Initialize Git
git init
```

---

### STEP 2: Create Your .gitignore

Create a file called `.gitignore` in your project root:

```
venv/
__pycache__/
*.pyc
.env
.DS_Store
*.egg-info/
dist/
*.ipynb_checkpoints
```

---

### STEP 3: Build the Data Fetcher (`src/data_fetcher.py`)

This is the messenger — it talks to NASA and brings back raw data.

```python
"""
data_fetcher.py
Handles all communication with the NASA POWER API.
"""
import requests
import pandas as pd
from datetime import datetime, timedelta


NASA_BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
MISSING_VALUE = -999.0


def get_date_range(days_back: int = 60) -> tuple[str, str]:
    """Returns start and end date strings for the API call."""
    end_date = datetime.today()
    start_date = end_date - timedelta(days=days_back)
    return start_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d")


def fetch_climate_data(
    latitude: float,
    longitude: float,
    start_date: str = None,
    end_date: str = None,
    days_back: int = 60
) -> dict:
    """
    Fetches PRECTOTCORR and GWETROOT from NASA POWER API.

    Args:
        latitude: Farm GPS latitude (e.g., 0.28 for Kakamega)
        longitude: Farm GPS longitude (e.g., 34.75 for Kakamega)
        start_date: Optional. Format: "YYYYMMDD"
        end_date: Optional. Format: "YYYYMMDD"
        days_back: Number of days of history to fetch if dates not specified

    Returns:
        dict with keys 'precipitation' and 'soil_moisture',
        each a pandas Series indexed by date.
    """
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
        raise ConnectionError("NASA POWER API timed out after 15 seconds.")
    except requests.exceptions.HTTPError as e:
        raise ConnectionError(f"NASA POWER API returned error: {e}")

    raw = response.json()
    parameters = raw["properties"]["parameter"]

    # Parse precipitation
    precip_raw = parameters["PRECTOTCORR"]
    precip = pd.Series(precip_raw)
    precip.index = pd.to_datetime(precip.index, format="%Y%m%d")
    precip = precip.replace(MISSING_VALUE, pd.NA).fillna(0.0)

    # Parse soil moisture
    soil_raw = parameters["GWETROOT"]
    soil = pd.Series(soil_raw)
    soil.index = pd.to_datetime(soil.index, format="%Y%m%d")
    soil = soil.replace(MISSING_VALUE, pd.NA)

    return {
        "precipitation": precip,
        "soil_moisture": soil,
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date
    }
```

---

### STEP 4: Build the Onset Engine (`src/onset_engine.py`)

This is the brain — it reads rainfall data and classifies the onset.

```python
"""
onset_engine.py
Implements the True/False rainfall onset detection logic.

Scientific basis:
  Mugalavai et al. (2008): onset = first day after season start where
  cumulative rainfall >= 20mm within 1-2 days, with no dry spell
  (7+ consecutive days < 1mm) in the following 30 days.
"""
import pandas as pd
from enum import Enum


class OnsetResult(Enum):
    TRUE_ONSET = "True Onset"
    FALSE_ONSET = "False Onset"
    NO_ONSET = "No Onset Detected"
    INSUFFICIENT_DATA = "Insufficient Data"


# Thresholds derived from literature (Mugalavai et al., 2008)
RAINFALL_THRESHOLD_MM = 20.0      # Cumulative rain over window to qualify
ONSET_WINDOW_DAYS = 2             # Days to accumulate rainfall
DRY_SPELL_THRESHOLD_MM = 1.0      # Daily rainfall below this = dry day
DRY_SPELL_CONSECUTIVE_DAYS = 7    # Consecutive dry days = dry spell
VALIDATION_WINDOW_DAYS = 30       # Days to look ahead for dry spells


def detect_dry_spell(
    rain_series: pd.Series,
    threshold_mm: float = DRY_SPELL_THRESHOLD_MM,
    consecutive_days: int = DRY_SPELL_CONSECUTIVE_DAYS
) -> bool:
    """
    Checks if a dry spell exists in the given rainfall series.

    A dry spell = `consecutive_days` or more days where daily rainfall
    is below `threshold_mm`.

    Args:
        rain_series: pandas Series of daily rainfall values
        threshold_mm: Rain below this = dry day (default: 1.0mm)
        consecutive_days: Length of dry spell to detect (default: 7)

    Returns:
        True if dry spell detected, False otherwise
    """
    consecutive = 0
    for value in rain_series:
        if pd.isna(value) or value < threshold_mm:
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
    Finds all candidate onset events: dates where cumulative rain
    over `window_days` meets or exceeds `threshold_mm`.

    Returns:
        Boolean Series where True = candidate onset date
    """
    rolling_sum = rain_series.rolling(window=window_days, min_periods=1).sum()
    return rolling_sum >= threshold_mm


def classify_onset(rain_series: pd.Series) -> dict:
    """
    Main classification function. Analyzes a rainfall time series and
    returns the onset classification result.

    Args:
        rain_series: pandas Series indexed by date, daily rainfall in mm

    Returns:
        dict with keys:
          'result': OnsetResult enum value
          'onset_date': date of detected onset or None
          'cumulative_rain': mm of rain that triggered the detection
          'dry_spell_found': bool
          'summary': human-readable description
    """
    if len(rain_series) < ONSET_WINDOW_DAYS + VALIDATION_WINDOW_DAYS:
        return {
            "result": OnsetResult.INSUFFICIENT_DATA,
            "onset_date": None,
            "cumulative_rain": None,
            "dry_spell_found": None,
            "summary": "Not enough data to make a classification. "
                       "At least 32 days of data required."
        }

    candidates = find_onset_candidates(rain_series)
    candidate_dates = rain_series[candidates].index

    if len(candidate_dates) == 0:
        return {
            "result": OnsetResult.NO_ONSET,
            "onset_date": None,
            "cumulative_rain": 0,
            "dry_spell_found": False,
            "summary": "No rainfall event has exceeded the 20mm threshold. "
                       "Rains have not yet started in this region."
        }

    # Evaluate each candidate from most recent backwards
    for onset_date in reversed(candidate_dates):
        # Get the validation window (next 30 days after onset)
        validation_start = onset_date
        validation_end = onset_date + pd.Timedelta(days=VALIDATION_WINDOW_DAYS)
        validation_window = rain_series[
            (rain_series.index > validation_start) &
            (rain_series.index <= validation_end)
        ]

        # Calculate the cumulative rain at this onset date
        window_start = onset_date - pd.Timedelta(days=ONSET_WINDOW_DAYS - 1)
        onset_window = rain_series[
            (rain_series.index >= window_start) &
            (rain_series.index <= onset_date)
        ]
        cumulative = onset_window.sum()

        # Check for dry spell in validation window
        if len(validation_window) >= DRY_SPELL_CONSECUTIVE_DAYS:
            dry_spell = detect_dry_spell(validation_window)
        else:
            # Validation window is incomplete — use what we have
            dry_spell = detect_dry_spell(validation_window)

        if dry_spell:
            return {
                "result": OnsetResult.FALSE_ONSET,
                "onset_date": onset_date.strftime("%B %d, %Y"),
                "cumulative_rain": round(float(cumulative), 2),
                "dry_spell_found": True,
                "summary": (
                    f"A rainfall event of {round(float(cumulative), 1)}mm was detected "
                    f"around {onset_date.strftime('%B %d')}. However, a dry spell of "
                    f"7 or more days was detected in the following 30 days. "
                    f"Status: FALSE ONSET. Do NOT plant yet."
                )
            }
        else:
            return {
                "result": OnsetResult.TRUE_ONSET,
                "onset_date": onset_date.strftime("%B %d, %Y"),
                "cumulative_rain": round(float(cumulative), 2),
                "dry_spell_found": False,
                "summary": (
                    f"A confirmed True Onset was detected. "
                    f"{round(float(cumulative), 1)}mm of rain fell around "
                    f"{onset_date.strftime('%B %d')}, with no dry spell in "
                    f"the following period. SAFE TO PLANT."
                )
            }

    return {
        "result": OnsetResult.NO_ONSET,
        "onset_date": None,
        "cumulative_rain": 0,
        "dry_spell_found": False,
        "summary": "No conclusive onset detected in the current data window."
    }
```

---

### STEP 5: Build the Irrigation Engine (`src/irrigation_engine.py`)

```python
"""
irrigation_engine.py
Analyzes root zone soil moisture (GWETROOT) and advises on irrigation.

GWETROOT scale:
  0.0 - 0.29  → Dry (irrigate)
  0.30 - 0.70 → Optimal
  0.71 - 1.0  → Saturated (do not irrigate)
"""
import pandas as pd
from enum import Enum


class IrrigationStatus(Enum):
    IRRIGATE = "Irrigate Today"
    OPTIMAL = "Soil Moisture Optimal"
    SATURATED = "Soil is Saturated - Do Not Irrigate"
    NO_DATA = "Soil Moisture Data Unavailable"


CRITICAL_MOISTURE_THRESHOLD = 0.30   # Below this → irrigate
SATURATION_THRESHOLD = 0.70          # Above this → stop irrigating


def classify_soil_moisture(soil_series: pd.Series) -> dict:
    """
    Analyzes soil moisture data and returns irrigation advisory.

    Args:
        soil_series: pandas Series indexed by date, GWETROOT values (0.0–1.0)

    Returns:
        dict with keys:
          'status': IrrigationStatus enum
          'current_value': latest GWETROOT reading
          'moisture_percent': value as percentage (0–100%)
          'moisture_category': 'Dry', 'Optimal', or 'Saturated'
          'summary': human-readable advisory
    """
    # Drop NaN and get most recent reading
    clean = soil_series.dropna()

    if len(clean) == 0:
        return {
            "status": IrrigationStatus.NO_DATA,
            "current_value": None,
            "moisture_percent": None,
            "moisture_category": "Unknown",
            "summary": "Soil moisture data is unavailable for this location. "
                       "Please try again later."
        }

    current = float(clean.iloc[-1])
    moisture_percent = round(current * 100, 1)

    if current < CRITICAL_MOISTURE_THRESHOLD:
        status = IrrigationStatus.IRRIGATE
        category = "Dry"
        summary = (
            f"Root zone soil moisture is critically low at {moisture_percent}%. "
            f"Plants are at risk of water stress. Irrigate today."
        )
    elif current >= SATURATION_THRESHOLD:
        status = IrrigationStatus.SATURATED
        category = "Saturated"
        summary = (
            f"Root zone soil moisture is at {moisture_percent}% — soil is saturated. "
            f"Do not irrigate. Excess water may cause root rot."
        )
    else:
        status = IrrigationStatus.OPTIMAL
        category = "Optimal"
        summary = (
            f"Root zone soil moisture is at {moisture_percent}% — within the optimal range. "
            f"No irrigation needed today."
        )

    return {
        "status": status,
        "current_value": round(current, 3),
        "moisture_percent": moisture_percent,
        "moisture_category": category,
        "summary": summary
    }
```

---

### STEP 6: Build the Flask App (`app/app.py`)

```python
"""
app.py
Flask web application for ROPIAS.
Serves the farmer dashboard and orchestrates the data pipeline.
"""
from flask import Flask, render_template, request, jsonify
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_fetcher import fetch_climate_data
from onset_engine import classify_onset, OnsetResult
from irrigation_engine import classify_soil_moisture, IrrigationStatus

app = Flask(__name__)


# Kenya bounding box for input validation
KENYA_LAT_MIN, KENYA_LAT_MAX = -5.0, 5.0
KENYA_LON_MIN, KENYA_LON_MAX = 34.0, 42.0


def validate_coordinates(lat: float, lon: float) -> bool:
    """Validates that coordinates fall within Kenya's bounding box."""
    return (
        KENYA_LAT_MIN <= lat <= KENYA_LAT_MAX and
        KENYA_LON_MIN <= lon <= KENYA_LON_MAX
    )


@app.route("/", methods=["GET"])
def index():
    """Renders the main dashboard."""
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    """
    Main analysis endpoint.
    Accepts lat/lon, fetches NASA data, runs both engines,
    returns JSON result for the frontend.
    """
    try:
        data = request.get_json()
        lat = float(data.get("latitude"))
        lon = float(data.get("longitude"))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid coordinates provided."}), 400

    if not validate_coordinates(lat, lon):
        return jsonify({
            "error": "Coordinates are outside Kenya's bounds. "
                     "Latitude: -5 to 5, Longitude: 34 to 42."
        }), 400

    # Fetch data from NASA
    try:
        climate_data = fetch_climate_data(
            latitude=lat,
            longitude=lon,
            days_back=60
        )
    except ConnectionError as e:
        return jsonify({"error": str(e)}), 503

    rain = climate_data["precipitation"]
    soil = climate_data["soil_moisture"]

    # Run onset engine
    onset = classify_onset(rain)

    # Run irrigation engine
    irrigation = classify_soil_moisture(soil)

    # Prepare chart data (last 14 days of rainfall)
    rain_14 = rain.tail(14)
    chart_labels = [d.strftime("%b %d") for d in rain_14.index]
    chart_values = [round(float(v), 2) for v in rain_14.values]

    # Map results to frontend colors
    onset_color_map = {
        OnsetResult.TRUE_ONSET: "green",
        OnsetResult.FALSE_ONSET: "red",
        OnsetResult.NO_ONSET: "grey",
        OnsetResult.INSUFFICIENT_DATA: "yellow"
    }

    return jsonify({
        "onset": {
            "result": onset["result"].value,
            "color": onset_color_map[onset["result"]],
            "onset_date": onset["onset_date"],
            "cumulative_rain": onset["cumulative_rain"],
            "summary": onset["summary"]
        },
        "irrigation": {
            "status": irrigation["status"].value,
            "moisture_percent": irrigation["moisture_percent"],
            "moisture_category": irrigation["moisture_category"],
            "summary": irrigation["summary"]
        },
        "chart": {
            "labels": chart_labels,
            "rainfall_values": chart_values
        }
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
```

---

### STEP 7: Write Tests (`tests/test_onset_engine.py`)

```python
"""
Tests for the onset detection engine.
Uses synthetic data to verify correct classification.
"""
import pandas as pd
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from onset_engine import classify_onset, detect_dry_spell, OnsetResult


def make_series(values: list, start: str = "2022-03-01") -> pd.Series:
    """Helper: creates a pandas Series with a date index."""
    dates = pd.date_range(start=start, periods=len(values), freq="D")
    return pd.Series(values, index=dates)


class TestDrySpellDetection:
    def test_detects_7_day_dry_spell(self):
        rain = make_series([5, 5, 0, 0, 0, 0, 0, 0, 0, 5])
        assert detect_dry_spell(rain) is True

    def test_no_dry_spell_when_rain_continues(self):
        rain = make_series([5, 5, 3, 2, 1, 4, 5, 2, 3, 1])
        assert detect_dry_spell(rain) is False

    def test_6_dry_days_is_not_a_dry_spell(self):
        rain = make_series([5, 0, 0, 0, 0, 0, 0, 5])
        # 6 consecutive dry days — below the 7-day threshold
        assert detect_dry_spell(rain) is False


class TestOnsetClassification:
    def test_true_onset_detected(self):
        """30mm over 2 days, then steady rain = True Onset."""
        values = (
            [0] * 10 +           # 10 quiet days
            [15, 16] +           # 31mm cumulative onset event
            [3, 2, 4, 2, 3, 2, 1, 2, 3, 4] * 3  # steady drizzle after
        )
        series = make_series(values)
        result = classify_onset(series)
        assert result["result"] == OnsetResult.TRUE_ONSET

    def test_false_onset_detected(self):
        """30mm over 2 days, then 8-day dry spell = False Onset."""
        values = (
            [0] * 10 +           # 10 quiet days
            [15, 16] +           # 31mm onset event
            [0, 0, 0, 0, 0, 0, 0, 0] +  # 8-day dry spell!
            [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        )
        series = make_series(values)
        result = classify_onset(series)
        assert result["result"] == OnsetResult.FALSE_ONSET

    def test_no_onset_when_rain_too_low(self):
        """Rain never exceeds 20mm cumulative = No Onset."""
        values = [1.5] * 45  # 1.5mm per day, never cumulates to 20mm in 2 days
        series = make_series(values)
        result = classify_onset(series)
        assert result["result"] == OnsetResult.NO_ONSET
```

---

### STEP 8: Set Up GitHub Repository

```bash
# In your ropias/ folder:

# 1. Create README.md
touch README.md

# 2. Stage all files
git add .

# 3. First commit
git commit -m "Initial commit: ROPIAS data science pipeline"

# 4. Create repo on GitHub (go to github.com → New Repository → name it 'ropias')

# 5. Connect local repo to GitHub
git remote add origin https://github.com/YOUR_USERNAME/ropias.git

# 6. Push
git branch -M main
git push -u origin main
```

---

## PART 7 — SIMILAR REPOSITORIES ON GITHUB

| Repository                           | What it does                                               | Link                                               |
| ------------------------------------ | ---------------------------------------------------------- | -------------------------------------------------- |
| `adrHuerta/rainfall_onset`           | Rainfall onset-cessation detection algorithm for Africa    | https://github.com/adrHuerta/rainfall_onset        |
| `kdmayer/nasa-power-api`             | Python script for NASA POWER historical data download      | https://github.com/kdmayer/nasa-power-api          |
| `alekfal/pynasapower`                | Python client library specifically for NASA POWER API      | https://github.com/alekfal/pynasapower             |
| `indrakalita/RainfallForecasting`    | ML-based rainfall prediction for Ghana (Africa case study) | https://github.com/indrakalita/RainfallForecasting |
| `KKulma/climate-change-data`         | Curated list of climate APIs and data science projects     | https://github.com/KKulma/climate-change-data      |
| GitHub Topics: `rainfall-prediction` | All public rainfall prediction projects                    | https://github.com/topics/rainfall-prediction      |
| GitHub Topics: `rainfall-data`       | All public rainfall data projects                          | https://github.com/topics/rainfall-data            |

---

## PART 8 — BLOG POSTS & LEARNING RESOURCES

| Title                                                                           | Source                      | Link                                                                                                                   |
| ------------------------------------------------------------------------------- | --------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Weather Data at Your Fingertips: A Beginner's Guide to NASA POWER API in Python | Medium (Adarsh Singh, 2024) | https://medium.com/@aadiray/weather-data-at-your-fingertips-a-beginners-guide-to-nasa-power-api-in-python-d62b7cff8922 |
| Climate Data at Your Command: Navigating NASA Power API with Python             | Medium (Axel Castro, 2024)  | https://medium.com/mcd-unison/climate-data-at-your-command-navigating-nasa-power-api-with-python-4e0d110e6b10          |
| NASA POWER API Tutorial (Official)                                              | NASA POWER Docs             | https://power.larc.nasa.gov/docs/tutorials/service-data-request/api/                                                   |
| Pandas Time Series Documentation                                                | Pandas Docs                 | https://pandas.pydata.org/docs/user_guide/timeseries.html                                                              |
| Flask Quickstart                                                                | Flask Docs                  | https://flask.palletsprojects.com/en/stable/quickstart/                                                                |

---

## PART 9 — REAL-WORLD INSTANCES OF THIS CONCEPT

### 9.1 ICPAC (IGAD Climate Prediction and Application Centre)

The Intergovernmental Authority on Development's climate center provides seasonal forecast data for East Africa — this is the institutional version of what ROPIAS does. They specifically track long rains and short rains onset timing across Kenya, Ethiopia, Uganda.

- **Website:** https://www.icpac.net/
- **Open data:** https://www.icpac.net/open-data-sources/

### 9.2 FEWS NET (Famine Early Warning Systems Network)

A USAID-funded global system that uses satellite rainfall data, soil moisture data, and vegetation indices to detect food security crises before they become famines. ROPIAS is a localized, grassroots version of this concept.

- **Website:** https://fews.net/

### 9.3 Farmonaut

An Indian agri-tech startup that provides satellite-based soil moisture monitoring and AI irrigation advisories to farmers through a mobile app — no physical sensors required. This is the closest commercial equivalent to ROPIAS.

- **Website:** https://farmonaut.com/

### 9.4 Kenya Meteorological Department (KMD)

The government authority that publishes seasonal forecast bulletins for the Long Rains and Short Rains in Kenya. ROPIAS essentially localizes their forecasts to individual GPS coordinates.

- **Website:** https://www.meteo.go.ke/

### 9.5 NASA SERVIR Program

A joint NASA/USAID program that builds satellite-based tools for climate adaptation in Africa and Asia — including tools for agricultural decision-making in East Africa.

- **Website:** https://www.nasa.gov/servir/

---

## PART 10 — REAL-WORLD DATA SCIENCE PROJECTS SIMILAR TO ROPIAS

| Project                                  | Description                                                                                                                  | Link                                                                |
| ---------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| **RainfallForecasting (Ghana)**          | ML-based rainfall prediction using ERA5 satellite data for tropical Africa. Same problem domain, more complex ML.            | https://github.com/indrakalita/RainfallForecasting                  |
| **NASA POWER Python Client**             | Open-source Python library for accessing the exact API this project uses                                                     | https://github.com/alekfal/pynasapower                              |
| **CHIRPS Rainfall Dataset**              | High-resolution satellite rainfall data used by researchers studying East African rainfall patterns                          | https://www.chc.ucsb.edu/data/chirps                                |
| **FOCUS-Africa Project (ScienceDirect)** | Academic paper assessing seasonal forecast skill for rain onset prediction across Africa — directly related research         | https://www.sciencedirect.com/science/article/pii/S2405880723000791 |
| **Agromet Advisory System (India)**      | India Meteorological Department's national system for crop advisories using satellite data — the government-scale equivalent | https://www.imdagrimet.gov.in/                                      |

---

## PART 11 — YOUR README.md TEMPLATE

When you push to GitHub, this README will be the first thing collaborators see:

````markdown
# 🌧️ ROPIAS — Rainfall Onset Prediction & Irrigation Advisory System

> A data-driven Python system that helps smallholder farmers in Kenya
> distinguish between True and False rainfall onsets, and receive
> satellite-based irrigation advisories.

## The Problem

Kenyan small-scale farmers lose crops every year to "false onsets" —
brief early rains that trick farmers into planting, followed by dry spells
that kill seeds. This system detects these false starts before they happen.

## How It Works

1. Farmer enters GPS coordinates
2. System fetches 60 days of satellite data from NASA POWER API
3. Onset Engine classifies rain as True, False, or No Onset
4. Irrigation Engine checks root zone soil moisture
5. Flask dashboard displays Green/Red/Blue advisory

## Data Source

NASA POWER API — free, no API key required, global coverage since 1981.
Parameters: `PRECTOTCORR` (precipitation), `GWETROOT` (root zone soil wetness)

## Tech Stack

- **Backend:** Python 3.x, Flask, Pandas, NumPy
- **Data:** NASA POWER REST API
- **Frontend:** Bootstrap 5, Chart.js
- **Testing:** pytest

## Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/ropias.git
cd ropias
pip install -r requirements.txt
python app/app.py
```
````

Then open http://localhost:5000

## Contributing

Pull requests welcome. See CONTRIBUTING.md for guidelines.
Areas where help is needed:

- Adding ML classification layer (Random Forest on historical onset data)
- Swahili translation of UI
- SMS alert integration (Africa's Talking API)
- Mobile PWA wrapper

## Scientific Basis

- Mugalavai et al. (2008): 20mm threshold, 7-day dry spell rule
- Kipkorir et al. (2007): Onset-cessation methodology for Western Kenya
- Nkunzimana et al. (2021): Variability of onset dates in East Africa

```

---

## PART 12 — WHAT TO BUILD NEXT (GROWTH ROADMAP)

Once the MVP is working, here is a logical progression:

### Phase 2 — Add Machine Learning
Instead of pure rule-based thresholds, train a classifier on 20+ years of
historical NASA data to predict onset probability. Start with:
- Logistic Regression (simplest, interpretable)
- Random Forest (better accuracy, still explainable)
- Input features: rolling rainfall sums, soil moisture trends, day-of-year

### Phase 3 — Historical Validation Dashboard
Pull data from 2018–2025 and run your engine on each year. Show a table
of how well your system would have performed vs actual crop outcomes.

### Phase 4 — SMS / WhatsApp Integration
Most Kenyan farmers don't use web browsers — they use SMS and WhatsApp.
- Africa's Talking API: https://africastalking.com/
- Twilio WhatsApp: https://www.twilio.com/

### Phase 5 — Swahili Localization
Translate the advisory output to Swahili using Python i18n (gettext).
"True Onset" → "Mvua ya Kweli Imeanza"
"False Onset" → "Mvua ya Udanganyifu — Subiri"

### Phase 6 — Deploy to Cloud
- Render (free tier): https://render.com/
- Railway: https://railway.app/
- PythonAnywhere (easiest for Flask): https://www.pythonanywhere.com/

---

*Guide written for the ROPIAS project — KCA University, BSc Data Science*
*Built with ❤️ for Kenya's smallholder farmers*
```
