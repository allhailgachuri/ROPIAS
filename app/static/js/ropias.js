// ropias.js — Frontend Master Logic Engine for the Dashboard
// Handles theming, geospatial extraction, toaster feedback, and Chart.js integrations.

document.addEventListener("DOMContentLoaded", () => {
    lucide.createIcons();
    initThemeSystem();
    initToastSystem();
});

/* ----------------------------------------------------
 * Theme Management (3-Mode Cycle System)
 * ---------------------------------------------------- */
const THEMES = ['system', 'light', 'dark'];
const THEME_LABELS = { system: 'System', light: 'Light', dark: 'Dark' };
const THEME_ICONS = { system: 'monitor', light: 'sun', dark: 'moon' };

function updateThemeUI(t) {
    const lbl = document.getElementById('theme-label');
    const iconEl = document.getElementById('theme-icon');
    if(lbl) lbl.textContent = THEME_LABELS[t];
    if(iconEl) {
        iconEl.innerHTML = '';
        const newIcon = document.createElement('i');
        newIcon.setAttribute('data-lucide', THEME_ICONS[t]);
        newIcon.className = "w-4 h-4";
        iconEl.appendChild(newIcon);
        lucide.createIcons();
    }
}

function cycleTheme() {
    let current = localStorage.getItem('ropias-theme') || 'system';
    let next = THEMES[(THEMES.indexOf(current) + 1) % THEMES.length];
    localStorage.setItem('ropias-theme', next);
    if(next === 'system') {
        const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
    } else {
        document.documentElement.setAttribute('data-theme', next);
    }
    updateThemeUI(next);
}

function initThemeSystem() {
    const saved = localStorage.getItem('ropias-theme') || 'system';
    updateThemeUI(saved);
}

/* ----------------------------------------------------
 * Toast Notification System
 * ---------------------------------------------------- */
function initToastSystem() {
    // If Flask passed flash messages in the DOM template, consume them.
    const flashes = document.querySelectorAll('.flask-flash-message');
    flashes.forEach(f => {
        showToast(f.dataset.message, f.dataset.category || 'info');
        f.remove();
    });
}

/**
 * Valid types: success, error, info, warning
 */
window.showToast = function(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if(!container) return;

    const toast = document.createElement('div');
    toast.className = `ropias-toast border-l-4`;
    
    let iconName = 'info';
    let borderColor = 'var(--text-secondary)';

    if(type === 'success') { iconName = 'check-circle'; borderColor = 'var(--green-safe)'; }
    if(type === 'error' || type === 'danger') { iconName = 'alert-triangle'; borderColor = 'var(--red-danger)'; }
    if(type === 'warning') { iconName = 'alert-circle'; borderColor = 'var(--amber-watch)'; }

    toast.style.borderLeftColor = borderColor;

    toast.innerHTML = `
        <i data-lucide="${iconName}" style="color: ${borderColor}; width: 20px; height: 20px; margin-top: 2px;"></i>
        <div style="flex-grow: 1; margin-right: 12px; line-height: 1.4;">${message}</div>
        <button onclick="this.parentElement.classList.add('hide'); setTimeout(()=>this.parentElement.remove(), 300)" style="background:none; border:none; color:var(--text-muted); cursor:pointer;">
            <i data-lucide="x" style="width: 16px; height: 16px;"></i>
        </button>
    `;

    container.appendChild(toast);
    lucide.createIcons();

    // Auto dismiss after 4 seconds
    setTimeout(() => {
        if(toast.parentElement) {
            toast.classList.add('hide');
            setTimeout(() => toast.remove(), 300);
        }
    }, 4000);
};

/* ----------------------------------------------------
 * Geospatial / Location Logic
 * ---------------------------------------------------- */
function useMyGPS() {
    if (!navigator.geolocation) {
        showToast("Geolocation is not supported by your browser.", "error");
        return;
    }
    
    showToast("Detecting precision coordinates...", "info");
    const latInp = document.getElementById('latitude-input');
    const lonInp = document.getElementById('longitude-input');
    
    if(latInp) latInp.closest('.ropias-input').style.opacity = '0.5';
    if(lonInp) lonInp.closest('.ropias-input').style.opacity = '0.5';

    navigator.geolocation.getCurrentPosition(
        (position) => {
            if(latInp) { latInp.value = position.coords.latitude.toFixed(4); latInp.closest('.ropias-input').style.opacity = '1'; }
            if(lonInp) { lonInp.value = position.coords.longitude.toFixed(4); lonInp.closest('.ropias-input').style.opacity = '1'; }
            showToast("📍 Location synchronized successfully.", "success");
        },
        (error) => {
            showToast("Failed to retrieve location. Please assure GPS is enabled.", "error");
            if(latInp) latInp.closest('.ropias-input').style.opacity = '1';
            if(lonInp) lonInp.closest('.ropias-input').style.opacity = '1';
        },
        { enableHighAccuracy: true, timeout: 5000 }
    );
}

/* ----------------------------------------------------
 * Value Animation (Count-Up) Logic
 * ---------------------------------------------------- */
function animateValue(obj, start, end, duration) {
    if(!obj) return;
    let startTimestamp = null;
    const isFloat = end % 1 !== 0;

    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        
        // easeOutExpo
        const ease = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
        
        let val = start + ease * (end - start);
        obj.innerHTML = isFloat ? val.toFixed(1) : Math.floor(val);
        
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

window.triggerCountUps = function() {
    document.querySelectorAll('.count-up').forEach(el => {
        const val = parseFloat(el.dataset.value || el.innerText);
        animateValue(el, 0, val, 1200);
    });
};

/* ----------------------------------------------------
 * Network State (Offline Banner)
 * ---------------------------------------------------- */
window.addEventListener('offline', () => {
    document.getElementById('offline-banner').style.display = 'block';
    showToast("Internet connection lost. You are operating offline.", "warning");
});

window.addEventListener('online', () => {
    document.getElementById('offline-banner').style.display = 'none';
    showToast("Internet reconnected. Live systems restored.", "success");
});
