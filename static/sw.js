const CACHE = 'masarify-v1';

self.addEventListener('install', e => {
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
});

self.addEventListener('fetch', e => {
  // فقط للـ GET requests
  if (e.request.method !== 'GET') return;

  e.respondWith(
    fetch(e.request).catch(() => caches.match(e.request))
  );
});
