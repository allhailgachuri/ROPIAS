/**
 * ROPIAS Service Worker
 * Caches the farmer dashboard for offline access.
 * When offline, serves the last cached advisory result.
 *
 * Strategy:
 *   - Static assets (CSS, JS, fonts): Cache First
 *   - /dashboard HTML: Network First with cache fallback
 *   - /analyze API: Network only (cannot work offline — needs NASA data)
 *   - Everything else: Network First
 */

const CACHE_NAME    = 'ropias-v1';
const OFFLINE_URL   = '/dashboard';

const STATIC_ASSETS = [
  '/static/css/ropias.css',
  '/static/js/ropias.js',
  '/static/manifest.json',
  '/static/icons/icon-192.png',
  'https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500&family=Source+Sans+3:wght@300;400;500&display=swap',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js'
];

// ── Install: pre-cache static assets ─────────────────────────────────────────
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      console.log('[ROPIAS SW] Pre-caching static assets');
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// ── Activate: clean up old caches ─────────────────────────────────────────────
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(key => key !== CACHE_NAME)
          .map(key => {
            console.log('[ROPIAS SW] Deleting old cache:', key);
            return caches.delete(key);
          })
      )
    )
  );
  self.clients.claim();
});

// ── Fetch: serve from cache when offline ──────────────────────────────────────
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  // Never intercept API calls — they need live NASA data
  if (url.pathname.startsWith('/analyze') ||
      url.pathname.startsWith('/api/') ||
      url.pathname.startsWith('/webhook/')) {
    return;
  }

  // Static assets: cache first
  if (STATIC_ASSETS.some(asset => event.request.url.includes(asset))) {
    event.respondWith(
      caches.match(event.request).then(cached => cached || fetch(event.request))
    );
    return;
  }

  // Dashboard HTML: network first, fall back to cache
  if (url.pathname === '/dashboard' || url.pathname === '/') {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
          return response;
        })
        .catch(() => {
          return caches.match(OFFLINE_URL).then(cached => {
            if (cached) return cached;
            // Absolute fallback: inline offline message
            return new Response(
              `<html><body style="font-family:sans-serif;text-align:center;padding:2rem">
                <h2>🌧️ ROPIAS</h2>
                <p>You are offline. Your last advisory has been cached.</p>
                <p>Reconnect to get the latest satellite data.</p>
              </body></html>`,
              { headers: { 'Content-Type': 'text/html' } }
            );
          });
        })
    );
    return;
  }

  // All other requests: network first
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});
