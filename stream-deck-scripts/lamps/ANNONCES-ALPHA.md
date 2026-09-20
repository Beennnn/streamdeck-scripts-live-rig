# Annonces alpha LumiDeck — prêtes à coller

Lien release : https://github.com/openlamp/lumideck/releases/tag/v0.1.0-alpha

---

## 1. Discord Makers Elgato (#showcase ou #plugins)

> 💡 **LumiDeck (alpha)** — control your smart lamps live from the Stream Deck, 100% local, zero cloud lag.
>
> I'm a keyboard player and built this to drive my stage lamps between songs. It targets the *cheapest* smart bulbs on the market (Tuya / Smart Life) and removes their only flaw — the cloud — by talking to them directly on the LAN.
>
> Keys for color / brightness / white / scenes / blackout, a live "Light Status" key, a multi-function dial, per-lamp targeting, snapshots, and even a MIDI bridge so Ableton can drive the lights.
>
> macOS (universal) alpha, self-contained: https://github.com/openlamp/lumideck/releases/tag/v0.1.0-alpha
> WLED support is in but untested — **testers with WLED hardware very welcome** 🙏
> Feedback super welcome, it's day one!

---

## 2. r/streamdeck (ou r/Elgato)

**Titre :** I built a local smart-lamp plugin for Stream Deck (Tuya/WLED, no cloud) — alpha out

> As a gigging musician I wanted my Stream Deck to run my stage lamps with zero latency and no internet. So I made **LumiDeck**: it drives cheap Tuya/Smart Life bulbs (and WLED) **100% locally**, as instant as the native app.
>
> - Keys: color, brightness, white temp, captured scenes, blackout/restore, countdown
> - A "Light Status" key that shows the real live state of each lamp
> - A dial where a press cycles color → brightness → power
> - Snapshots of the whole rig, fades, per-lamp/group targeting
> - Bonus: a MIDI bridge so Ableton/any DAW can drive the lights in sync
>
> macOS universal, self-contained (no Python to install):
> https://github.com/openlamp/lumideck/releases/tag/v0.1.0-alpha
>
> It's a day-one alpha — bug reports and ideas very welcome. WLED owners: I need testers!
> Under the hood it's a layered family (engine / Stream Deck / MIDI, one repo each):
> https://github.com/openlamp/openlamp

---

## 3. Forum / Discord WLED (#hardware-and-projects ou équivalent)

> Hi! I built **LumiDeck**, an Elgato Stream Deck plugin to control lamps locally. It speaks the **WLED JSON API** natively (plus a small superset I call *OpenLamp State*), so it can drive WLED devices — and it even exposes a WLED-compatible `/json/state` endpoint locally.
>
> Thing is: **I don't own any WLED hardware**, so the WLED path is written but unverified. If any of you would spend 10 minutes pointing it at a WLED bulb/strip and telling me what breaks, that would be hugely helpful 🙏
>
> Repo + macOS alpha: https://github.com/openlamp/lumideck
> OLS spec: https://github.com/openlamp/openlamp-engine-python/blob/main/OLS.md
> (Not affiliated with the WLED project — just building on your great open API.)

---

Rappel : poste depuis un moment où tu peux répondre aux premiers retours dans l'heure (l'engagement day-one compte).
