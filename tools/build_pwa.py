"""Builds the GitHub/offline version of Finanzgipfel from the artifact source (finanzen-app.html)."""
import re,json,os,hashlib
HERE=os.path.dirname(os.path.abspath(__file__))
SRC=os.path.join(HERE,'finanzen-app.html');OUT=os.path.dirname(HERE)
s=open(SRC).read()
def rep(a,b,cnt=1):
    global s
    assert s.count(a)==cnt,(a[:70],s.count(a));s=s.replace(a,b)
# --- document head ---
head='''<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="robots" content="noindex, nofollow, noarchive">
<meta name="googlebot" content="noindex, nofollow">
<meta name="theme-color" content="#0e1514" media="(prefers-color-scheme: dark)">
<meta name="theme-color" content="#eef2f1" media="(prefers-color-scheme: light)">
<meta name="description" content="Persönliche Budget-App. Alle Daten bleiben auf dem Gerät.">
<link rel="manifest" href="manifest.webmanifest?v=2">
'''
rep('<meta name="claude:viewport-fit-sides" content="cover">\n','')
rep('<div id="splash"','</head>\n<body>\n<div id="splash"')
s=head+s
rep('</script>\n','</script>\n</body>\n</html>\n') if s.rstrip().endswith('</script>') else None
# --- texts ---
rep('Deine Finanzdaten werden geladen.<br><span class="small">Falls nichts erscheint: in claude.ai anmelden und die App über deinen Link öffnen.</span>','Deine Finanzdaten werden geladen.')
rep('<div class="small muted">Deine Daten werden mit deinem claude.ai-Konto gespeichert und sind auf allen Geräten gleich.</div>',
    '<div class="small muted">Deine Daten sind nur auf diesem Gerät gespeichert, nirgends online. Mach deshalb regelmässig eine Sicherung.</div>')
rep('''    <button class="btn full" id="export" style="margin-top:10px">''','''    <button class="btn full" id="restore" style="margin-top:10px">Sicherung laden</button>
    <div class="small muted" style="margin-top:6px">Ersetzt alle Daten auf diesem Gerät durch die gewählte Sicherung.</div>
    <button class="btn full" id="export" style="margin-top:10px">''')
# bind restore button next to backup binding
m=re.search(r'on\("#backup",[^\n]*\n',s); assert m, 'backup binding'
s=s[:m.end()]+'  on("#restore",()=>pickBackup());\n'+s[m.end():]
# --- local storage layer replacing the claude.ai database ---
local=r'''
/* ---------- local storage (this device only) ----------
   Same small interface the app used before (doc().set / onSnapshot, collection().onSnapshot),
   backed by localStorage. Each document is one key "fg:<path>". */
const LS="fg:";
const localDb=(()=>{const subs=[];
  const read=p=>{try{const v=localStorage.getItem(LS+p);return v?JSON.parse(v):null}catch(e){return null}};
  const keys=pre=>{const o=[];for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i);if(k&&k.startsWith(LS+pre+"/"))o.push(k.slice(LS.length))}return o};
  const snapDoc=p=>{const d=read(p);return{exists:d!=null,data:()=>d,metadata:{fromCache:false}}};
  const snapCol=c=>({docs:keys(c).map(p=>({id:p.slice(c.length+1),data:()=>read(p)})),metadata:{fromCache:false}});
  const notify=p=>subs.forEach(s=>{if(s.doc===p)s.cb(snapDoc(p));else if(s.col&&p.startsWith(s.col+"/"))s.cb(snapCol(s.col))});
  return{
    doc:p=>({set:async d=>{try{localStorage.setItem(LS+p,JSON.stringify(d))}catch(e){throw{message:"Speicher voll oder gesperrt"}}notify(p)},
      onSnapshot:(cb)=>{subs.push({doc:p,cb});cb(snapDoc(p))}}),
    collection:c=>({onSnapshot:(cb)=>{subs.push({col:c,cb});cb(snapCol(c))}}),
    clearAll:()=>{const ks=[];for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i);if(k&&k.startsWith(LS))ks.push(k)}ks.forEach(k=>localStorage.removeItem(k))},
    has:()=>read("settings/main")!=null}})();
const fileDownloads={save:async({filename,data})=>{const blob=new Blob([data],{type:filename.endsWith(".csv")?"text/csv;charset=utf-8":"application/json"});
  const u=URL.createObjectURL(blob),a=document.createElement("a");a.href=u;a.download=filename;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),4000)}};
function pickBackup(){const i=document.createElement("input");i.type="file";i.accept=".json,application/json";
  i.onchange=()=>{const f=i.files&&i.files[0];if(!f)return;const r=new FileReader();r.onload=()=>restoreBackup(String(r.result));r.readAsText(f)};i.click()}
function restoreBackup(txt){let d;try{d=JSON.parse(txt)}catch(e){toast("Diese Datei ist keine Finanzgipfel-Sicherung");return}
  if(!d||d.app!=="Finanzgipfel"||!d.settings||typeof d.months!=="object"){toast("Diese Datei ist keine Finanzgipfel-Sicherung");return}
  const n=Object.keys(d.months).length,when=d.created?new Date(d.created).toLocaleDateString("de-CH",{day:"numeric",month:"long",year:"numeric"}):"";
  if(!localDb.has()){doRestore(d,n);return}
  openSheet(`<h3>Sicherung laden?</h3><div class="small">Sicherung${when?" vom "+when:""} mit ${n} Monaten. Sie <b>ersetzt alle Daten</b> auf diesem Gerät.</div>
    <div class="row actions" style="gap:8px"><button class="btn" id="rCancel">Abbrechen</button><button class="btn primary" style="flex:1" id="rOk">Ersetzen</button></div>`,el=>{
    el.querySelector("#rCancel").onclick=()=>closeSheet();el.querySelector("#rOk").onclick=()=>{closeSheet();doRestore(d,n)}})}
function doRestore(d,n){
  try{localDb.clearAll();localStorage.setItem(LS+"settings/main",JSON.stringify(d.settings));
    for(const[k,v] of Object.entries(d.months))localStorage.setItem(LS+"months/"+k,JSON.stringify(v));
    if(d.vermoegen)localStorage.setItem(LS+"vermoegen/all",JSON.stringify(d.vermoegen));
    localStorage.removeItem("fin-cache3")}catch(e){toast("Laden fehlgeschlagen: Speicher voll?");return}
  try{sessionStorage.setItem("fg-restored",String(n))}catch(e){}location.reload()}
function startEmpty(){const y=todayYear();localDb.doc("settings/main").set({startYear:y,salary:[{from:y*100+1,netto:0,brutto:0}],fix:[],fixYear:[],cats:["Lebensmittel","Auswärts Essen","Freizeit","Transport","Kleider","Gesundheit","Geschenke","Diverses"],lebensmittel:0,hobbyStart:{[y]:0},steuerJahr:{}})}
function welcome(){const b=$("#boot");if(!b)return;b.classList.remove("empty");b.style.textAlign="center";
  b.innerHTML=`<div class="mid" style="margin-bottom:6px">Willkommen bei Finanzgipfel</div><div class="small muted" style="margin-bottom:14px">Hast du schon eine Sicherung? Dann lade sie hier, und alle deine Daten sind da.</div>
    <button class="btn primary full" id="wRestore">Sicherung laden</button><button class="btn full" id="wEmpty" style="margin-top:10px">Ohne Daten beginnen</button>
    <div class="small muted" style="margin-top:12px">Deine Daten bleiben nur auf diesem Gerät.</div>`;
  $("#wRestore").onclick=pickBackup;$("#wEmpty").onclick=()=>{startEmpty();toast("Lege los: zuerst unter Planung deinen Lohn eintragen")}}
'''
rep('/* ---------- boot ---------- */','/* ---------- boot ---------- */'+local)
rep('''  db=await(window.claude?.use?window.claude.use("db"):Promise.resolve(null)).catch(()=>null);
  downloads=await(window.claude?.use?window.claude.use("downloads"):Promise.resolve(null)).catch(()=>null);
  if(!db){setSync();if(!S.settings)$("#boot").innerHTML="Keine Verbindung zum Speicher.<br><span class='small'>Öffne die App über deinen claude.ai-Link und melde dich an.</span>";return}''',
'''  db=localDb;downloads=fileDownloads;
  try{navigator.storage&&navigator.storage.persist&&navigator.storage.persist()}catch(e){}
  try{const n=sessionStorage.getItem("fg-restored");if(n){sessionStorage.removeItem("fg-restored");setTimeout(()=>toast(`Sicherung geladen · ${n} Monate`),2600)}}catch(e){}''')
rep('''else if(!S.settings){$("#boot").innerHTML="Noch keine Daten gespeichert."}''','''else if(!S.settings){welcome()}''')
# second pick with same file confirms: re-route
# sync label
rep('''t.textContent=pending?"Speichert…":"Gespeichert"}''','''t.textContent=pending?"Speichert…":"Auf dem Gerät"}''')
# service worker registration
rep('</body>\n</html>','''<script>if("serviceWorker" in navigator&&location.protocol!=="file:")addEventListener("load",()=>navigator.serviceWorker.register("sw.js").catch(()=>{}));</script>
</body>
</html>''')
os.makedirs(OUT,exist_ok=True)
open(OUT+'/index.html','w').write(s)
ver=hashlib.sha1((s+open(__file__).read()).encode()).hexdigest()[:10]
open(OUT+'/sw.js','w').write(f'''/* Finanzgipfel offline cache. The version changes with every build, so phones pick up updates. */
const VERSION="fg-{ver}";
const CORE=["./","index.html","manifest.webmanifest?v=2","icon-192.png","icon-512.png","icon-maskable-512.png","apple-touch-icon.png"];
self.addEventListener("install",e=>{{e.waitUntil(caches.open(VERSION).then(c=>c.addAll(CORE)).then(()=>self.skipWaiting()))}});
self.addEventListener("activate",e=>{{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==VERSION).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))}});
self.addEventListener("fetch",e=>{{const r=e.request;if(r.method!=="GET")return;const u=new URL(r.url);
  if(u.origin===location.origin){{
    if(u.pathname.endsWith(".webmanifest")){{e.respondWith(fetch(r).catch(()=>caches.match(r)));return}}
    if(r.mode==="navigate"){{e.respondWith(fetch(r).then(res=>{{const cp=res.clone();caches.open(VERSION).then(c=>c.put("index.html",cp));return res}}).catch(()=>caches.match("index.html")));return}}
    e.respondWith(caches.match(r).then(hit=>hit||fetch(r).then(res=>{{const cp=res.clone();caches.open(VERSION).then(c=>c.put(r,cp));return res}})));return}}
  if(/fonts\\.(googleapis|gstatic)\\.com$/.test(u.hostname)){{
    e.respondWith(caches.open("fg-fonts").then(c=>c.match(r).then(hit=>hit||fetch(r).then(res=>{{c.put(r,res.clone());return res}}))))}}
}});
''')
json.dump({"id":"/finanzgipfel-app/","name":"Finanzgipfel","short_name":"Finanzgipfel","description":"Persönliche Budget-App, offline auf dem Gerät.","lang":"de-CH",
 "start_url":"./","scope":"./","display":"standalone","orientation":"portrait","background_color":"#1b2a49","theme_color":"#1b2a49",
 "icons":[{"src":"icon-192.png","sizes":"192x192","type":"image/png","purpose":"any"},{"src":"icon-512.png","sizes":"512x512","type":"image/png","purpose":"any"},
          {"src":"icon-maskable-512.png","sizes":"512x512","type":"image/png","purpose":"maskable"}]},open(OUT+'/manifest.webmanifest','w'),ensure_ascii=False,indent=1)
open(OUT+'/robots.txt','w').write("User-agent: *\nDisallow: /\n")
open(OUT+'/.nojekyll','w').write("")
print('built',len(s),ver)
