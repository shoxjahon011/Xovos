const CACHE = 'xovos-v9';
const SHELL = ['/', '/static/places/style.css'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys =>
    Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))));
  self.clients.claim();
});

// Tarmoq birinchi, internet bo'lmasa keshdan
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  if (req.headers.has('range')) return;                 // video bo'laklari
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;           // tashqi xarita plitkalari
  if (url.pathname.startsWith('/admin')) return;
  if (/\.(mp4|webm|mov|m4v)$/i.test(url.pathname)) return;

  e.respondWith(
    fetch(req).then(res => {
      if (res.ok) {
        const copy = res.clone();
        caches.open(CACHE).then(c => c.put(req, copy));
      }
      return res;
    }).catch(() => caches.match(req))
  );
});