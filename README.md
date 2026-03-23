# 🌧️ ROPIAS — Rainfall Onset Prediction & Irrigation Advisory System

> A data-driven Python system that helps smallholder farmers in Kenya
> distinguish between **True** and **False** rainfall onsets, and receive
> satellite-based irrigation advisories — no hardware required.

---

## The Problem

Kenyan small-scale farmers lose crops every year to **false onsets** —
brief early rains that trick farmers into planting, followed by dry spells
that kill seeds before they germinate. This system detects these false
starts using NASA satellite data before a farmer commits to planting.

---

## How It Works

```
Farmer enters GPS coordinates
         ↓
Python fetches 60 days of data from NASA POWER API
         ↓
Onset Engine: cumulative rain ≥ 20mm in 2 days?
              + no dry spell (7+ days < 1mm) in next 30 days?
         ↓
Irrigation Engine: GWETROOT < 0.30? → Irrigate
         ↓
Flask dashboard shows Green / Red / Blue advisory
```

---

## Project Structure

```
ropias/
├── src/
│   ├── data_fetcher.py        ← NASA POWER API communication
│   ├── onset_engine.py        ← True/False onset classification
│   ├── irrigation_engine.py   ← Soil moisture advisory
│   └── __init__.py
├── app/
│   ├── app.py                 ← Flask web app
│   └── templates/
│       └── index.html         ← Farmer dashboard UI
├── notebooks/
│   ├── 01_nasa_api_exploration.ipynb
│   └── 02_onset_engine_development.ipynb
├── tests/
│   ├── test_onset_engine.py
│   └── test_irrigation_engine.py
├── data/                      ← Saved charts and JSON summaries
├── requirements.txt
└── README.md
```

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/ropias.git
cd ropias

# 2. Create virtual environment
python -m venv venv
source venv/Scripts/activate   # Windows
source venv/bin/activate        # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the web app
python app/app.py

# 5. Open in browser
# http://localhost:5000
```

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Data Source

**NASA POWER API** — free, no API key required, global coverage since 1981.

| Parameter | Meaning | Unit |
|---|---|---|
| `PRECTOTCORR` | Corrected daily precipitation | mm/day |
| `GWETROOT` | Root zone soil wetness (top 1m) | fraction 0–1 |

API Docs: https://power.larc.nasa.gov/docs/

---

## Scientific Basis

| Paper | Threshold Used |
|---|---|
| Mugalavai et al. (2008) | 20mm / 2-day window / 7-day dry spell |
| Nkunzimana et al. (2021) | 20mm / 3-day window / 7-day dry spell |
| Kipkorir et al. (2007) | 40mm / 4-day window / 30-day validation |

This system uses the Mugalavai consensus as primary threshold.

---

## Tech Stack

- **Backend:** Python 3.x, Flask, Pandas, NumPy
- **Data:** NASA POWER REST API
- **Frontend:** Bootstrap 5, Chart.js
- **Testing:** pytest

---

## Contributing

Pull requests welcome. Areas where help is needed:

- [ ] ML classification layer (Random Forest on historical onset data)
- [ ] Swahili translation of the UI
- [ ] SMS/WhatsApp alerts via Africa's Talking API
- [ ] Extended coverage beyond Kenya
- [ ] Historical validation dashboard (2015–2025)
- [ ] Progressive Web App (PWA) mobile wrapper

---

## Academic Context

BSc Data Science Project — KCA University, Nairobi, Kenya.
Supervisor: Fredrick Omondi

---

*Data source: NASA POWER (power.larc.nasa.gov) — public domain under NASA open data policy.*