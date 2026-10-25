/* Finanzgipfel offline cache. The version changes with every build, so phones pick up updates. */
const VERSION="fg-5953d2c88c";
const CORE=["./","index.html","manifest.webmanifest?v=2","icon-192.png","icon-512.png","icon-maskable-512.png","apple-touch-icon.png"];
self.addEventListener("install",e=>{e.waitUntil(caches.open(VERSION).then(c=>c.addAll(CORE)).then(()=>self.skipWaiting()))});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==VERSION).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener("fetch",e=>{const r=e.request;if(r.method!=="GET")return;const u=new URL(r.url);
  if(u.origin===location.origin){
    if(u.pathname.endsWith(".webmanifest")){e.respondWith(fetch(r).catch(()=>caches.match(r)));return}
    if(r.mode==="navigate"){e.respondWith(fetch(r).then(res=>{const cp=res.clone();caches.open(VERSION).then(c=>c.put("index.html",cp));return res}).catch(()=>caches.match("index.html")));return}
    e.respondWith(caches.match(r).then(hit=>hit||fetch(r).then(res=>{const cp=res.clone();caches.open(VERSION).then(c=>c.put(r,cp));return res})));return}
  if(/fonts\.(googleapis|gstatic)\.com$/.test(u.hostname)){
    e.respondWith(caches.open("fg-fonts").then(c=>c.match(r).then(hit=>hit||fetch(r).then(res=>{c.put(r,res.clone());return res}))))}
});
