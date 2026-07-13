"""Local web dashboard — a global rig-state view with per-item fix/relaunch.

Pure stdlib (http.server). The page auto-refreshes the state (read-only checks);
fixes and the full preflight are explicit POSTs triggered by buttons, and honour
the dry-run toggle end to end. Bind to 127.0.0.1 only — never exposed off-machine.
"""

from __future__ import annotations

import json
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import checks, launch, remedy

# The audio check shells out to system_profiler (~1s); cache it so a page polling
# every few seconds doesn't hammer it. Apps + MIDI stay live (they're cheap).
_audio_cache: dict = {"ts": 0.0, "res": None}
_AUDIO_TTL = 15.0

_GROUP = {"app:": "Apps", "midi?:": "MIDI optionnel", "midi:": "MIDI requis", "audio": "Audio"}


def _group_of(key: str) -> str:
    for prefix, name in _GROUP.items():
        if key.startswith(prefix):
            return name
    return "Autre"


def build_state(cfg: dict, with_audio: bool = True) -> dict:
    results = checks.check_apps(cfg) + checks.check_midi(cfg)
    if with_audio:
        now = time.time()
        if _audio_cache["res"] is None or now - _audio_cache["ts"] > _AUDIO_TTL:
            _audio_cache["res"] = checks.check_audio(cfg)
            _audio_cache["ts"] = now
        results.append(_audio_cache["res"])
    items = []
    for r in results:
        rem = remedy.resolve(cfg, r)
        items.append({
            **r.to_dict(),
            "group": _group_of(r.key),
            "remedy": rem.label if (rem and r.status != checks.OK) else None,
        })
    status = checks.worst(results)
    return {
        "status": status,
        "fails": sum(1 for r in results if r.status == checks.FAIL),
        "warns": sum(1 for r in results if r.status == checks.WARN),
        "total": len(results),
        "items": items,
    }


class _Handler(BaseHTTPRequestHandler):
    cfg: dict = {}

    def log_message(self, *_):  # silence default request logging
        pass

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj: dict, code: int = 200) -> None:
        self._send(code, json.dumps(obj).encode("utf-8"), "application/json; charset=utf-8")

    def _read_body(self) -> dict:
        n = int(self.headers.get("Content-Length", 0) or 0)
        if not n:
            return {}
        try:
            return json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return {}

    def do_GET(self) -> None:
        if self.path == "/" or self.path.startswith("/index"):
            self._send(200, PAGE.encode("utf-8"), "text/html; charset=utf-8")
        elif self.path.startswith("/api/state"):
            self._json(build_state(self.cfg))
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self) -> None:
        body = self._read_body()
        dry = bool(body.get("dry", False))
        if self.path == "/api/fix":
            rem = remedy.resolve_key(self.cfg, body.get("key", ""))
            if rem is None:
                self._json({"ok": False, "message": "Aucune action automatique pour cet élément."})
                return
            ok, msg = rem.run(dry)
            self._json({"ok": ok, "message": msg})
        elif self.path == "/api/preflight":
            logs: list[str] = []
            launch.bring_up(self.cfg, log=logs.append, dry_run=dry)
            self._json({"ok": True, "message": "\n".join(logs)})
        else:
            self._json({"ok": False, "message": "route inconnue"}, code=404)


def serve(cfg: dict, port: int = 8765, open_browser: bool = True) -> None:
    handler = type("Handler", (_Handler,), {"cfg": cfg})
    httpd = ThreadingHTTPServer(("127.0.0.1", port), handler)
    url = f"http://127.0.0.1:{port}/"
    print(f"Dashboard rig → {url}  (Ctrl-C pour arrêter)")
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard arrêté.")
    finally:
        httpd.server_close()


# --- the page (self-contained: inline CSS + JS, no external requests) ----------
PAGE = r"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>🎹 Rig — état</title>
<style>
  :root{color-scheme:dark;--bg:#0d0f14;--card:#161a22;--line:#242a36;--tx:#e7ebf2;--mut:#8a93a3;
        --ok:#2ecc71;--warn:#f4b942;--fail:#ff5468;--accent:#4a9eff}
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--tx);font:15px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
  header{position:sticky;top:0;background:linear-gradient(#0d0f14,#0d0f14ee);padding:16px 20px;border-bottom:1px solid var(--line);z-index:5}
  h1{margin:0 0 4px;font-size:19px}
  .sub{color:var(--mut);font-size:13px}
  .banner{margin:12px 0 0;padding:12px 16px;border-radius:10px;font-weight:600;display:flex;gap:10px;align-items:center}
  .banner.ok{background:#123322;color:var(--ok)} .banner.warn{background:#332a12;color:var(--warn)} .banner.fail{background:#3a1620;color:var(--fail)}
  .bar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-top:12px}
  button{font:inherit;border:1px solid var(--line);background:var(--card);color:var(--tx);padding:8px 14px;border-radius:9px;cursor:pointer}
  button:hover{border-color:var(--accent)} button:active{transform:translateY(1px)}
  button.primary{background:var(--accent);border-color:var(--accent);color:#03122b;font-weight:600}
  button.fix{background:transparent;border-color:var(--fail);color:var(--fail);padding:6px 12px;font-size:13px}
  button.fix:hover{background:var(--fail);color:#2a0009}
  label.dry{display:flex;gap:6px;align-items:center;color:var(--mut);font-size:13px;user-select:none}
  main{padding:8px 20px 40px;max-width:820px;margin:0 auto}
  .grp{margin-top:22px} .grp h2{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--mut);margin:0 0 8px}
  .row{display:flex;align-items:center;gap:12px;background:var(--card);border:1px solid var(--line);border-left-width:4px;border-radius:10px;padding:11px 14px;margin-bottom:8px}
  .row.ok{border-left-color:var(--ok)} .row.warn{border-left-color:var(--warn)} .row.fail{border-left-color:var(--fail)}
  .ic{font-size:18px;width:22px;text-align:center}
  .lab{flex:1;min-width:0} .lab .t{font-weight:500} .lab .d{color:var(--mut);font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  #log{white-space:pre-wrap;background:#0a0c11;border:1px solid var(--line);border-radius:10px;padding:12px;margin-top:18px;font:12px/1.5 ui-monospace,Menlo,monospace;color:var(--mut);max-height:200px;overflow:auto;display:none}
  .stamp{color:var(--mut);font-size:12px}
  @media(max-width:520px){.row{flex-wrap:wrap}.lab .d{white-space:normal}}
</style></head><body>
<header>
  <h1>🎹 Rig — état global</h1>
  <div class="sub">Vue auto-rafraîchie (lecture seule). Les actions sont des clics explicites.</div>
  <div id="banner" class="banner warn">…chargement</div>
  <div class="bar">
    <button class="primary" onclick="preflight()">▶ Préflight complet</button>
    <button onclick="refresh()">↻ Rafraîchir</button>
    <label class="dry"><input type="checkbox" id="dry"> mode simulation (dry-run)</label>
    <span class="stamp" id="stamp"></span>
  </div>
</header>
<main><div id="groups"></div><div id="log"></div></main>
<script>
const IC={ok:"✅",warn:"⚠️",fail:"❌"};
const dry=()=>document.getElementById("dry").checked;
function logline(t){const l=document.getElementById("log");l.style.display="block";l.textContent=(new Date().toLocaleTimeString()+"  "+t+"\n"+l.textContent).slice(0,4000);}
async function refresh(){
  const y=window.scrollY;
  let s;try{s=await(await fetch("/api/state")).json();}catch(e){return;}
  const b=document.getElementById("banner");b.className="banner "+s.status;
  b.textContent=s.status==="ok"?"✅ Rig prêt — tout est vert."
    :s.status==="warn"?`⚠️ Rig jouable — ${s.warns} avertissement(s).`
    :`❌ Rig PAS prêt — ${s.fails} bloquant(s), ${s.warns} avertissement(s).`;
  const groups={};for(const it of s.items){(groups[it.group]=groups[it.group]||[]).push(it);}
  const order=["Apps","MIDI requis","Audio","MIDI optionnel","Autre"];
  const host=document.getElementById("groups");host.innerHTML="";
  for(const g of order){if(!groups[g])continue;
    const sec=document.createElement("div");sec.className="grp";
    sec.innerHTML=`<h2>${g}</h2>`;
    for(const it of groups[g]){
      const row=document.createElement("div");row.className="row "+it.status;
      row.innerHTML=`<div class="ic">${IC[it.status]}</div>
        <div class="lab"><div class="t">${it.label}</div>${it.detail?`<div class="d">${it.detail}</div>`:""}</div>`;
      if(it.remedy){const btn=document.createElement("button");btn.className="fix";btn.textContent=it.remedy;
        btn.onclick=()=>fix(it.key,it.remedy);row.appendChild(btn);}
      sec.appendChild(row);
    }host.appendChild(sec);
  }
  document.getElementById("stamp").textContent="maj "+new Date().toLocaleTimeString();
  window.scrollTo(0,y);
}
async function fix(key,label){
  logline(`→ ${label}${dry()?" (dry-run)":""}…`);
  const r=await(await fetch("/api/fix",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({key,dry:dry()})})).json();
  logline((r.ok?"✔ ":"✖ ")+(r.message||"").replace(/\n/g,"  |  "));
  setTimeout(refresh,800);
}
async function preflight(){
  logline(`▶ préflight${dry()?" (dry-run)":""}…`);
  const r=await(await fetch("/api/preflight",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({dry:dry()})})).json();
  logline((r.message||"").replace(/\n/g,"  |  "));
  setTimeout(refresh,1200);
}
refresh();setInterval(refresh,4000);
</script></body></html>"""
