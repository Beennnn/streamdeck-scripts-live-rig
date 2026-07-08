# 🎹 Live Rig — a keyboardist's centrally-controlled stage setup

How I run keys for a 4-piece original pop-rock band: one MacBook, one keyboard, a couple
of Stream Decks — and everything (sounds, mixer, stage lights, backing structure) driven
from a single pane of glass, switching automatically per song.

This repo documents the **architecture, the control logic, and the config-as-code approach**
behind the setup. It's a showcase, not a product — but everything here is what actually runs
on stage.

> ⚠️ The device-specific config (profiles, SysEx dumps, secrets) lives in private repos.
> What's public here is the **readable logic + the story**.

---

## The idea

On stage I don't want to touch the laptop. Every song needs different sounds, a different
mixer scene, sometimes different lighting — and it has to happen in **one button press**,
reliably, with no menu diving. So the whole rig is:

- **Centralized** — one controller surface drives sounds + mixer + lights
- **Song-aware** — one profile per song, switched automatically
- **Config-as-code** — the entire wired state is versioned in git, backed up three ways
- **Recoverable** — a bad update or a dead SD card doesn't cost me a gig

---

## Signal flow

```
                    ┌───────────────────────────────────────────────┐
     Keyboard  ─────► MacBook / Ableton Live                         │
   (MIDI + audio)   │   • Omnisphere / Keyscape (Spectrasonics)      │
                    │   • per-song racks, backing structure          │
                    └───────────┬───────────────────────┬───────────┘
                                │ audio                  │ MIDI control
                                ▼                        ▲
                    ┌───────────────────┐    ┌───────────┴───────────┐
                    │  XR18 digital mixer│    │  Bome MIDI Translator │
                    │  (scene per song)  │    │  (virtual MIDI ports, │
                    └─────────┬──────────┘    │   routing + watchdog) │
                              │ audio          └───────────▲──────────┘
                              ▼                            │ MIDI
                         PA / IEM                ┌─────────┴──────────┐
                                                 │   Stream Decks     │
   Stage lights ◄──── (Tuya / WLED) ◄──────────┤   (trevligaspel    │
                       lamp controller           │    MIDI plugin)    │
                                                 └────────────────────┘
```

**One press on a Stream Deck button** can, at once: switch the Ableton song, recall the XR18
scene, and set the stage lights — because the button emits MIDI that Bome fans out to every
destination.

---

## Components

| Layer | Gear | Role |
|---|---|---|
| **Keys** | Yamaha P-225 | main controller + weighted feel |
| **Brain** | MacBook + Ableton Live | sound engine, per-song racks |
| **Sounds** | Omnisphere, Keyscape | flagship synths / keys |
| **Control** | Stream Deck XL + Plus (+ virtual) | the single pane of glass |
| **Plugin** | trevligaspel MIDI (Stream Deck) | turns buttons into MIDI (see `stream-deck-scripts/`) |
| **Routing** | Bome MIDI Translator | virtual ports, fan-out, keep-alive watchdog |
| **Mixer** | Behringer XR18 | scene-per-song, IEM + FOH |
| **Expression** | TEControl breath, FCB1010 | hands-free control |
| **Lights** | Tuya / WLED lamps | stage ambiance, driven from the Stream Deck |

---

## The control logic (what's in this repo)

### `stream-deck-scripts/` — the button DSL

The trevligaspel plugin runs a small text DSL per button. A few examples of what's here:

- **`nav/`** — setlist navigation: `sd_next`, `sd_prev`, `sd_song`, `sd_setlist`, `sd_run_songs`
  → move through the set, one song at a time, hands-free
- **`track/`** — `sd_track1..8`: per-channel mixer strips (VU feedback, fader, select, mute)
  mapped to buttons — a physical mixer surface on the Stream Deck
- **`silence/`** — panic/clean: `sd_main_mute`, `sd_omni_stop`, `sd_clean`
  → instant "everything off" for between-song silence
- **`XR18/sd_talk`** — talkback mic toggle to the mixer
- **`sd_background.txt`** — defines the setlists as variables (the "which songs, in what order")

These are the actual scripts running on stage — readable MIDI logic, no magic.

### Song switching — the ghost-app trick

Stream Deck switches profiles based on which app is "frontmost". So each song gets a tiny
**ghost AppleScript app** (does nothing but quit itself); the Stream Deck profile is bound to
that app's path via `AppIdentifier`. Pressing a song button "launches" the ghost → Stream Deck
flips to that song's page. Creating a new song's switcher = copy the template app. Simple,
robust, no plugin dependency.

### Lights from the Stream Deck

A small controller (Python/JS) exposes Tuya/WLED lamps as Stream Deck buttons, so lighting
cues are just more buttons in the same setlist flow. *(Controller code kept private — it holds
device keys — but the integration point is a Stream Deck button like any other.)*

---

## Config-as-code & backup philosophy

Nothing about this rig is allowed to live in only one place:

- **Stable device config** (MIDI routing, controller mappings, mixer scenes, SysEx dumps) →
  **git-versioned** (private `rig-config` repo). Small, stable, diffable, restorable with a clone.
- **Stream Deck profiles** (churny, rewritten on every button edit) → **cloud sync** (delta-friendly)
  + a **weekly git snapshot** for history.
- **Home-automation / analysis scripts** → their own git repos, CI-checked.

A weekly `launchd` job snapshots the live config into git and pushes it. A dedicated
recovery script re-materializes everything if a cloud-sync eviction ever blanks the config
mid-gig. The result: **the laptop is disposable** — a fresh machine + a few `git clone`s
rebuilds the whole rig.

---

## Screenshots

*(coming soon — the actual Stream Deck pages + a "button press → sound + light reacts" GIF)*

See [`screenshots/`](screenshots/).

---

## Why I built it this way

Playing keys live is already enough to think about. The rig's job is to **disappear** — to make
"next song" a single, reliable gesture, and to never be the reason a set stops. Treating the
whole setup as versioned, backed-up, recoverable code is what makes it trustworthy enough to
forget about once the count-in starts.
