/* 
    ropias.js 
    Frontend scripting for ROPIAS 
*/

// --- State ---
let currentLang = 'en';
let chartInstance = null;
let cropsData = {};

const dict = {
    en: {
        'location_setup': '📍 Location Setup',
        'city_search': 'City or Town',
        'use_gps': 'Use My GPS',
        'crop_type': 'Active Crop',
        'analyze_btn': 'Analyze Farm →',
        'analyzing': 'Connecting to NASA POWER API...'
    },
    sw: {
        'location_setup': '📍 Eneo Lako',
        'city_search': 'Mji / Jiji',
        'use_gps': 'Tumia GPS Yangu',
        'crop_type': 'Aina ya Mimea',
        'analyze_btn': 'Changanua Shamba →',
        'analyzing': 'Inavuta data kutoka kwa setilaiti za NASA...'
    }
};

// --- Initialization ---
document.addEventListener("DOMContentLoaded", async () => {
    try {
        const res = await fetch('/api/crops');
        const data = await res.json();
        cropsData = data.categories;
        populateCropSelect();
    } catch(e) { console.error("Failed to load crops", e); }
    
    // Bind Translation Toggle
    document.getElementById('lang-toggle').addEventListener('click', () => {
        currentLang = currentLang === 'en' ? 'sw' : 'en';
        applyTranslations();
    });
});

function applyTranslations() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if(dict[currentLang] && dict[currentLang][key]) {
            el.innerText = dict[currentLang][key];
        }
    });
}

function populateCropSelect() {
    const select = document.getElementById('crop-select');
    if(!select) return; // If on another page
    
    select.innerHTML = '';
    
    for (const [category, crops] of Object.entries(cropsData)) {
        const group = document.createElement('optgroup');
        group.label = category;
        crops.forEach(crop => {
            const opt = document.createElement('option');
            opt.value = crop.id;
            opt.textContent = crop.display_name;
            group.appendChild(opt);
        });
        select.appendChild(group);
    }
    
    select.addEventListener('change', updateCropInfo);
    if(select.options.length > 0) updateCropInfo();
}

function updateCropInfo() {
    const val = document.getElementById('crop-select').value;
    let selectedCrop = null;
    
    for (const crops of Object.values(cropsData)) {
        const found = crops.find(c => c.id === val);
        if(found) { selectedCrop = found; break; }
    }
    
    if(selectedCrop) {
        document.getElementById('crop-info-card').classList.remove('d-none');
        document.getElementById('info-crop-name').innerHTML = `<i class="fa-solid fa-seedling" style="color: var(--teal);"></i> ${selectedCrop.display_name}`;
        document.getElementById('info-crop-desc').innerText = selectedCrop.description;
        document.getElementById('info-moisture').innerText = `${selectedCrop.optimal_moisture_min*100}% - ${selectedCrop.optimal_moisture_max*100}%`;
        document.getElementById('info-stages').innerText = selectedCrop.water_sensitive_stages.map(s => s.replace('_', ' ')).join(', ');
        document.getElementById('info-season').innerText = selectedCrop.planting_season.map(s => s.replace('_', ' ')).join(', ');
    }
}

// --- Geolocation ---
function useGPS() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                document.getElementById('lat-input').value = pos.coords.latitude.toFixed(4);
                document.getElementById('lon-input').value = pos.coords.longitude.toFixed(4);
                document.getElementById('city-input').value = ''; 
            },
            (err) => { alert("Failed to get GPS: " + err.message); }
        );
    } else {
        alert("Geolocation is not supported by this browser.");
    }
}

// --- Analysis Engine ---
async function analyzeData() {
    const city = document.getElementById('city-input').value;
    const lat = document.getElementById('lat-input').value;
    const lon = document.getElementById('lon-input').value;
    const crop = document.getElementById('crop-select').value || "maize";

    if (!city && (!lat || !lon)) {
        alert("Please enter a city or GPS coordinates.");
        return;
    }

    document.getElementById('results').classList.add('d-none');
    document.getElementById('loading').classList.remove('d-none');

    const payload = city ? { city, crop } : { latitude: parseFloat(lat), longitude: parseFloat(lon), crop };

    try {
        const res = await fetch('/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (res.ok) {
            if(data.location) {
                document.getElementById('lat-input').value = (data.location.latitude).toFixed(4);
                document.getElementById('lon-input').value = (data.location.longitude).toFixed(4);
            }
            populateDashboard(data);
            await fetchForecast(data.location.latitude, data.location.longitude);
            document.getElementById('loading').classList.add('d-none');
            document.getElementById('results').classList.remove('d-none');
        } else {
            alert(data.error || "Analysis failed.");
            document.getElementById('loading').classList.add('d-none');
        }
    } catch (e) {
        alert("Network error: " + e.message);
        document.getElementById('loading').classList.add('d-none');
    }
}

function populateDashboard(data) {
    // Onset Panel
    const onsetDiv = document.getElementById('onset-panel');
    onsetDiv.className = `advisory-banner banner-${data.onset.color}`;
    document.getElementById('onset-title').innerText = data.onset.result;
    document.getElementById('onset-summary').innerText = data.onset.summary;
    
    if (data.onset.ml_metadata) {
        document.getElementById('onset-confidence').innerText = `ML Conf: ${Math.round(data.onset.ml_metadata.confidence * 100)}%`;
        document.getElementById('onset-confidence').style.display = 'inline-block';
    } else {
        document.getElementById('onset-confidence').style.display = 'none';
    }

    // Irrigation Panel
    const irrDiv = document.getElementById('irrigation-panel');
    let bannerColor = data.irrigation.color;
    if (bannerColor === 'none') bannerColor = 'true';
    irrDiv.className = `glass-card h-100 advisory-banner banner-${bannerColor}`;
    
    document.getElementById('soil-pct').innerText = `${data.irrigation.moisture_percent}%`;
    document.getElementById('soil-cat').innerText = data.irrigation.moisture_category;
    
    let trendIcon = 'fa-arrows-left-right text-muted';
    let trendColor = 'var(--teal)';
    if (data.irrigation.trend === 'rising') { trendIcon = 'fa-arrow-trend-up'; trendColor = 'var(--onset-true)'; }
    if (data.irrigation.trend === 'falling') { trendIcon = 'fa-arrow-trend-down'; trendColor = 'var(--onset-false)'; }
    
    document.getElementById('soil-trend').innerHTML = `<i class="fa-solid ${trendIcon}" style="color: ${trendColor}"></i> Trend: ${data.irrigation.trend.charAt(0).toUpperCase() + data.irrigation.trend.slice(1)}`;
    document.getElementById('soil-trend').style.color = trendColor;
    
    document.getElementById('irrigation-summary').innerText = data.irrigation.summary;

    // Chart
    drawChart(data.chart.labels, data.chart.rainfall, data.chart.soil_moisture);
}

// --- Forecast Engine ---
async function fetchForecast(lat, lon) {
    try {
        const res = await fetch('/api/forecast', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ latitude: lat, longitude: lon })
        });
        const data = await res.json();
        
        if (data.forecast_risk) {
            const strip = document.getElementById('forecast-strip');
            strip.innerHTML = '';
            const today = new Date();
            
            data.forecast_risk.daily_risk_scores.forEach((score, i) => {
                const dayDate = new Date(today);
                dayDate.setDate(today.getDate() + i + 1);
                const dayName = dayDate.toLocaleDateString('en-US', { weekday: 'short' });
                
                let dotClass = 'dot-green';
                if(score > 70) dotClass = 'dot-red';
                else if (score > 40) dotClass = 'dot-amber';
                
                strip.innerHTML += `
                    <div class="risk-pill">
                        <span class="risk-day">${dayName}</span>
                        <div class="risk-dot ${dotClass}"></div>
                        <span class="risk-val">Risk ${score}</span>
                    </div>
                `;
            });
        }
    } catch(e) { console.error("Forecast failed:", e); }
}

// --- Charting ---
function drawChart(labels, rainData, soilData) {
    const ctx = document.getElementById('trendsChart').getContext('2d');
    
    if (chartInstance) { chartInstance.destroy(); }
    
    const style = getComputedStyle(document.body);
    const navy = style.getPropertyValue('--navy').trim() || '#2F4156';
    const teal = style.getPropertyValue('--teal').trim() || '#567C8D';
    const sky = style.getPropertyValue('--sky').trim() || '#C8D9E6';
    const textPrimary = style.getPropertyValue('--color-text-primary').trim() || '#333';
    
    chartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Rainfall (mm)',
                    data: rainData,
                    backgroundColor: navy,
                    borderRadius: 4,
                    order: 2,
                    yAxisID: 'y'
                },
                {
                    label: 'Soil Moisture (%)',
                    data: soilData,
                    type: 'line',
                    borderColor: teal,
                    backgroundColor: `${sky}40`, // 40 is hex opacity
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    order: 1,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            scales: {
                y: { type: 'linear', display: true, position: 'left', title: {display: true, text: 'Rain (mm)', color: textPrimary} },
                y1: { type: 'linear', display: true, position: 'right', min: 0, max: 100, grid: {drawOnChartArea: false}, title: {display: true, text: 'Moisture (%)', color: textPrimary} },
                x: { grid: { color: 'rgba(0,0,0,0.05)' } }
            },
            plugins: {
                legend: { labels: { color: textPrimary, font: {family: "'Source Sans 3', sans-serif"} } }
            }
        }
    });
}

// --- Utilities ---
function shareDashboard() {
    html2canvas(document.getElementById('capture-area'), {
        backgroundColor: getComputedStyle(document.body).getPropertyValue('--color-bg-page').trim(),
        scale: 2
    }).then(canvas => {
        const link = document.createElement('a');
        link.download = 'ropias-advisory.png';
        link.href = canvas.toDataURL();
        link.click();
    });
}

async function subscribeAlert() {
    const phone = document.getElementById('sub-phone').value;
    const lat = document.getElementById('lat-input').value;
    const lon = document.getElementById('lon-input').value;
    
    if(!phone || !lat || !lon) {
        alert("Please run an analysis on your farm first, and provide a phone number.");
        return;
    }
    
    try {
        const res = await fetch('/api/alerts/subscribe', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone, latitude: lat, longitude: lon })
        });
        const data = await res.json();
        alert(data.message || data.status);
    } catch(e) {
        alert("Failed to subscribe: " + e.message);
    }
}
