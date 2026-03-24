# 🌧️ ROPIAS — Rainfall Onset Prediction & Irrigation Advisory System

> A data-driven Python system that helps smallholder farmers in Kenya 
> distinguish between **True** and **False** rainfall onsets and receive
> crop-specific irrigation advisories — no hardware required.

---

## 🌾 Expanded Crop Coverage
ROPIAS now supports the entire spectrum of Kenyan agricultural production, calibrated specifically for each crop's physiological water needs.

| Category | Supported Crops |
|---|---|
| **Cereals** | Maize, Wheat, Rice, Sorghum, Millet, Barley |
| **Legumes** | Beans, Cowpea, Green Gram, Pigeon Pea, Groundnuts, Soybean |
| **Root Crops** | Cassava, Sweet Potato, Irish Potato, Yam, Arrow Root |
| **Vegetables** | Kale (Sukuma Wiki), Tomato, Onion, Cabbage, Spinach, Carrot, Capsicum, Eggplant |
| **Cash Crops** | Coffee, Tea, Sugarcane, Sunflower, Cotton, Sisal |
| **Fruits** | Banana, Mango, Avocado, Passion Fruit, Watermelon, Pineapple |
| **Fodder** | Napier Grass, Rhodes Grass |

---

## 🎨 Design System & Color Palette
The ROPIAS interface utilizes a premium glassmorphic design system tailored for high legibility and semantic trust.

**Typography**
- **Display**: Playfair Display (Serif)
- **Body**: Source Sans 3 (Sans-serif)

**Core Hex Codes**
- `--navy` (`#2F4156`): Primary dark tone for headers and primary CTAs.
- `--teal` (`#567C8D`): Secondary accent for icons, active states, and soil moisture trends.
- `--sky`  (`#C8D9E6`): Accessible pastel for input backgrounds and passive data fills.
- `--beige` (`#F5EFEB`): Light mode page background ensuring warm contrast.
- `--onset-true` (`#2E7D52`): Semantic Green (Safe to plant).
- `--onset-false` (`#C0392B`): Semantic Red (False onset / Do not plant).

---

## 🔬 Scientific Basis: Crop Thresholds
Thresholds are dynamically routed in `src/crop_registry.py` based on established agronomic science specific to the East African climate.

- **True Onset Thresholds**: Cereals like Maize require a sharp `20mm` accumulation over 2 days to trigger germination. Drought-tolerant crops like Millet require only `12mm` over 3 days. Extremely thirsty crops like Rice require `30mm`.
- **Dry Spell Tolerance**: If a dry spell occurs immediately after planting, germination fails. Maize is heavily penalized by a `7-day` dry spell, whereas deep-rooted Sorghum can tolerate up to `14 days`.
- **Critical Soil Moisture (GWETROOT)**: Roots in the top 1M require different saturation levels to prevent wilting. Avocados suffer below `32%` (0.32), while Sisal easily stabilizes at `12%` (0.12). 

---

## 🚀 Deployment Instructions
This application uses a sophisticated Gunicorn/Flask pipeline optimized for cloud environments. It handles NASA API timeouts automatically if configured correctly.

### Option A — Railway.app (Recommended / Easiest)
1. Install the Railway CLI: `npm i -g @railway/cli`
2. Create an account at [Railway.app](https://railway.app/) and link your GitHub.
3. The repository already contains a `railway.toml` and `Procfile`.
4. Run `railway login`, then `railway link`, and finally `railway up`.
5. **Environment Variables**: In your Railway Dashboard, under "Variables", add:
   - `DATABASE_URL=sqlite:////tmp/ropias.db`
   - `NASA_API_TIMEOUT=120`
6. Click "Generate Domain" in the settings tab to get your live public URL!

### Option B — PythonAnywhere (Flask-Native setup)
1. Create a free account at [PythonAnywhere](https://www.pythonanywhere.com/).
2. Open a Bash Console and run:
   ```bash
   git clone https://github.com/allhailgachuri/ropias.git
   cd ropias
   mkvirtualenv --python=/usr/bin/python3.11 ropias-env
   pip install -r requirements.txt
   ```
3. Navigate to the **Web Tab**, click "Add a new web app", select "Manual Configuration", and choose Python 3.11.
4. Edit the WSGI configuration file:
   ```python
   import sys
   path = '/home/yourusername/ropias'
   if path not in sys.path:
       sys.path.append(path)
   from app.app import app as application
   ```
5. Set `DATABASE_URL` in the `.env` file within the repo and hit Reload!

### Option C — Render.com (Advanced / Docker-Ready)
1. Connect your GitHub repository to [Render](https://render.com).
2. The provided `render.yaml` handles the Blueprint. Render will automatically detect it.
3. **Build Command Configuration**: `pip install -r requirements.txt`
4. **Start Command**: `gunicorn -w 4 -b 0.0.0.0:10000 --timeout 120 app.app:app`
5. *Note: For persistent memory on Render, go to your dashboard Add-Ons, attach a Free PostgreSQL database, and replace the `DATABASE_URL` mapping in `render.yaml` with the provided Postgres internal connection string.*

**Verifying Deployment**: Visit `YOUR_APP_URL/health` to trigger a 200 OK JSON status check!

---

## 🔌 API Endpoints
The REST architecture is highly scalable and separated from the UI layer.

| Endpoint | Method | Payload | Returns |
|---|---|---|---|
| `/analyze` | `POST` | `{"city": "Nakuru", "crop": "maize"}` | Full onset detection, 14-day climate array, and ML confidence. |
| `/api/forecast` | `POST` | `{"latitude": -0.28, "longitude": 36.07}` | Real-time generated 7-day algorithmic risk trend. |
| `/api/crops` | `GET` | N/A | Categorized JSON array mapping `KENYA_CROPS` agronomic capabilities. |
| `/api/alerts/subscribe`| `POST`| `{"phone":"+254..", "latitude": -0.2}` | Stores user for daily 6AM Africa's Talking warnings. |

---

## 📸 Screenshots
*(Add high-resolution screenshots here showing the new UI)*
- `dashboard.png` - The glassmorphic farmer dashboard showing true onset detection for Sorghum.
- `crop_library.png` - The new grid-based Crop Reference document page.
- `sms_alert.png` - Real image of an Africa's Talking SMS arriving on a standard feature phone.

---

## 🤝 Contributing
ROPIAS was built as an academic requirement that ballooned into an industry-grade framework. Pull requests are highly welcome.

**Areas for collaboration:**
- [x] Integrate 30+ Kenyan crops with scientific moisture thresholds.
- [x] Glassmorphism Dashboard Redesign.
- [x] Cloud Deployment Configurations established.
- [ ] Implement a full asynchronous task queue (Celery + Redis) for massive SMS scale.
- [ ] Migrate `sqlite` to `PostgreSQL` for concurrent write handling.
- [ ] Expand the NASA parsing script using `Concurrent.Futures` to minimize the API lag.

---

*ROPIAS — Built for Kenya's 4 million smallholder farmers*  
*BSc Data Science Final Year Project — KCA University, Nairobi, Kenya*