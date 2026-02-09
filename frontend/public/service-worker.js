/* eslint-disable no-restricted-globals */

// This service worker can be customized!
// See https://developers.google.com/web/tools/workbox/modules/workbox-strategies
// for other available strategies.

const CACHE_NAME = 'aurora-sentinel-v3';
const urlsToCache = [
    '/',
    '/index.html',
    '/static/js/bundle.js',
    '/manifest.json'
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => cache.addAll(urlsToCache))
    );
    // Force the waiting service worker to become the active service worker
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('[Service Worker] Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    // Take control of all pages immediately
    return self.clients.claim();
});

self.addEventListener('fetch', (event) => {
    // Only intercept http/https requests
    if (!event.request.url.startsWith('http')) return;

    event.respondWith(
        caches.match(event.request)
            .then((cachedResponse) => {
                if (cachedResponse) return cachedResponse;

                return fetch(event.request).catch((err) => {
                    console.warn('[Service Worker] Fetch failed:', event.request.url, err);
                    // Optionally return a fallback or rethrow
                    throw err;
                });
            })
    );
});
