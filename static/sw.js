const CACHE = 'masarify-v2';

self.addEventListener('install', e => { self.skipWaiting(); });

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
});

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(fetch(e.request).catch(() => caches.match(e.request)));
});

// استقبال الإشعارات
self.addEventListener('push', e => {
  const data = e.data ? e.data.json() : {};
  const title = data.title || 'مصاريفي';
  const options = {
    body: data.body || '',
    icon: '/static/icon-192.png',
    badge: '/static/icon-192.png',
    dir: 'rtl',
    lang: 'ar',
    vibrate: [200, 100, 200],
    data: { url: data.url || '/' }
  };
  e.waitUntil(self.registration.showNotification(title, options));
});

// النقر على الإشعار
self.addEventListener('notificationclick', e => {
  e.notification.close();
  e.waitUntil(clients.openWindow(e.notification.data.url || '/'));
});
