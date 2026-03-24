/* 
    ropias.js 
    Frontend scripting for ROPIAS 
*/

// --- State ---
let currentLang = 'en';
let chartInstance = null;

const dict = {
    en: {
        'location_setup': '📍 Location Setup',
        'city_search': 'City or Town',
        'use_gps': 'Use My GPS',
        'crop_type': 'Crop Type',
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
document.getElementById('lang-toggle').addEventListener('click', () => {
    currentLang = currentLang === 'en' ? 'sw' : 'en';
    applyTranslations();
});

function applyTranslations() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if(dict[currentLang] && dict[currentLang][key]) {
            el.innerText = dict[currentLang][key];
        }
    });
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

    if (!city && (!lat || !lon)) {
        alert("Please enter a city or GPS coordinates.");
        return;
    }

    // Toggle UI State
    document.getElementById('results').classList.add('d-none');
    document.getElementById('loading').classList.remove('d-none');

    const payload = city ? { city } : { latitude: parseFloat(lat), longitude: parseFloat(lon) };

    try {
        const res = await fetch('/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (res.ok) {
            // Update Inputs to show returned coordinates if city was used
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
    onsetDiv.className = `glass-panel mb-4 animate-slide-up status-${data.onset.color}`;
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
    irrDiv.className = `glass-panel h-100 animate-slide-up status-${data.irrigation.color}`;
    document.getElementById('soil-pct').innerHTML = `${data.irrigation.moisture_percent}% <span class="fs-6 text-muted">${data.irrigation.moisture_category}</span>`;
    
    const trendIcon = data.irrigation.trend === 'rising' ? 'fa-arrow-trend-up text-success' : 
                      data.irrigation.trend === 'falling' ? 'fa-arrow-trend-down text-danger' : 
                      'fa-arrows-left-right text-muted';
    
    document.getElementById('soil-trend').innerHTML = `<i class="fa-solid ${trendIcon}"></i> Trend: ${data.irrigation.trend.charAt(0).toUpperCase() + data.irrigation.trend.slice(1)}`;
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
                
                let dotClass = 'low';
                if(score > 70) dotClass = 'critical';
                else if (score > 40) dotClass = 'high';
                else if (score > 20) dotClass = 'medium';
                
                strip.innerHTML += `
                    <div class="risk-day">
                        <span class="small fw-bold">${dayName}</span>
                        <div class="risk-dot ${dotClass}"></div>
                        <span class="small text-muted">${score}</span>
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
    
    chartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Rainfall (mm)',
                    data: rainData,
                    backgroundColor: 'rgba(59, 130, 246, 0.7)',
                    borderRadius: 4,
                    order: 2,
                    yAxisID: 'y'
                },
                {
                    label: 'Soil Moisture (%)',
                    data: soilData,
                    type: 'line',
                    borderColor: 'rgba(16, 185, 129, 1)',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
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
            interaction: { mode: 'index', intersect: false },
            scales: {
                y: { type: 'linear', display: true, position: 'left', title: {display: true, text: 'Rain (mm)', color: '#94a3b8'} },
                y1: { type: 'linear', display: true, position: 'right', min: 0, max: 100, grid: {drawOnChartArea: false}, title: {display: true, text: 'Moisture (%)', color: '#94a3b8'} },
                x: { grid: { color: 'rgba(255,255,255,0.05)' } }
            },
            plugins: {
                legend: { labels: { color: '#f8fafc' } }
            }
        }
    });
}

// --- Utilities ---
function shareDashboard() {
    html2canvas(document.getElementById('capture-area'), {
        backgroundColor: '#0f172a',
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

// PWA Service Worker Registration
if ('serviceWorker' in navigator) {
    // window.addEventListener('load', () => { navigator.serviceWorker.register('/sw.js'); });
}
