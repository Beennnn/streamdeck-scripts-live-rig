#!/usr/bin/env python3
"""bench.py — low-level single-lamp bench (Benoit 2026-07-04).
Raw tinytuya, ONE lamp, persistent socket, one colour every 8 s, ack timing
per command. No engine, no heals — the naked protocol. Ctrl+C or 12 min.
Requires the Stream Deck plugin to be STOPPED (single connection slot)."""
import json, os, sys, time
import tinytuya

HERE = os.path.dirname(os.path.abspath(__file__))
cfg = json.load(open(os.path.join(HERE, "tuya-lamps.json")))
name = sys.argv[1] if len(sys.argv) > 1 else "L2"
lamp = next(l for l in cfg["lamps"] if l["name"] == name)
ip = (lamp.get("ips") or {}).get(lamp.get("last", ""), "")
print(f"=== BENCH {name} @ {ip} — 1 couleur/8s, 12 min, Ctrl+C pour stopper ===")
d = tinytuya.BulbDevice(lamp["device_id"], ip, lamp["local_key"], version=3.5)
d.set_socketPersistent(True); d.set_socketTimeout(3); d.set_socketRetryLimit(1)
COLS = [("rouge", (230, 0, 40)), ("bleu", (0, 100, 200))]
times, errs = [], 0
t_end = time.time() + 12 * 60
i = 0
while time.time() < t_end:
    cname, (r, g, b) = COLS[i % 2]; i += 1
    t0 = time.monotonic()
    try:
        res = d.set_multiple_values({
            d.dpset["switch"]: True, d.dpset["mode"]: "colour",
            d.dpset["colour"]: d.rgb_to_hexvalue(r, g, b, d.dpset["value_hexformat"])},
            nowait=False)
        ms = (time.monotonic() - t0) * 1000
        bad = (isinstance(res, dict) and res.get("Error")) or not res
        if bad:
            errs += 1
            print(time.strftime("%H:%M:%S"), f"{cname:5s} ERREUR ({'vide' if not res else res.get('Error')}) apres {ms:.0f} ms")
        else:
            times.append(ms)
            print(time.strftime("%H:%M:%S"), f"{cname:5s} ack {ms:6.0f} ms")
    except Exception as e:
        errs += 1
        print(time.strftime("%H:%M:%S"), f"{cname:5s} EXCEPTION {str(e)[:60]}")
    time.sleep(8)
if times:
    ts = sorted(times)
    print(f"\n=== BILAN {name}: {len(times)} ok / {errs} err | mediane {ts[len(ts)//2]:.0f} ms | p95 {ts[int(len(ts)*0.95)]:.0f} ms | max {ts[-1]:.0f} ms ===")
os.system("open -a 'Elgato Stream Deck'")   # rend la main au plugin
