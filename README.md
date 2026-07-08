# 🎹 Live Rig — a keyboardist's centrally-controlled stage setup

How I run keys for a 4-piece original pop-rock band: one MacBook, one keyboard, a couple of
Stream Decks — and everything (sounds, mixer, stage lights, backing structure) driven from a
single pane of glass, switching automatically per song.

This repo documents the **architecture, the control logic, the gear, and the config-as-code
approach** behind the setup. It's a showcase, not a product — but everything here is what
actually runs on stage.

![Ableton Live](https://img.shields.io/badge/Ableton_Live-000000?logo=abletonlive&logoColor=white)
![Elgato Stream Deck](https://img.shields.io/badge/Elgato_Stream_Deck-1268DB?logo=elgato&logoColor=white)
![Bome](https://img.shields.io/badge/Bome_MIDI_Translator-FF6A00)
![Behringer XR18](https://img.shields.io/badge/Behringer_XR18-D32F2F)
![macOS](https://img.shields.io/badge/macOS-000000?logo=apple&logoColor=white)
![MIDI](https://img.shields.io/badge/MIDI-2.0-4B0082)

> ⚠️ The device-specific config (profiles, SysEx dumps, home-automation credentials) lives in
> private repos. What's public here is the **readable logic + the story + the gear**.

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

## The gear — what I play, and what I've tested

Over the years I've tried a lot of tools building this rig. Here's the current stage setup,
plus the alternatives I evaluated along the way.

### 🎛️ Sound engine & DAW

| Product | Role | Link |
|---|---|---|
| **Ableton Live** | host — per-song racks, backing structure, control surface | [ableton.com](https://www.ableton.com/live/) |
| **Spectrasonics Omnisphere** | flagship synth — pads, leads, textures | [spectrasonics.net](https://www.spectrasonics.net/products/omnisphere/) |
| **Spectrasonics Keyscape** | keyboards — Rhodes, Wurli, pianos | [spectrasonics.net](https://www.spectrasonics.net/products/keyscape/) |
| **Spectrasonics Trilian** | bass | [spectrasonics.net](https://www.spectrasonics.net/products/trilian/) |
| **IK Multimedia Hammond B-3X** | organ + Leslie | [ikmultimedia.com](https://www.ikmultimedia.com/products/hammondb3x/) |
| **Xfer Serum** · **Arturia Pigments** | wavetable synths (evaluated) | [xferrecords.com](https://xferrecords.com/products/serum) · [arturia.com](https://www.arturia.com/products/software-instruments/pigments/) |
| **Audio Modeling SWAM** | physical-modelled winds/strings | [audiomodeling.com](https://audiomodeling.com/) |
| **GG Audio Blue3** · **iZotope VocalSynth** | organ / vocal FX (tested) | [gg-audio.com](https://www.gg-audio.com/blue3.html) |

### 🎚️ Control surfaces & keyboards

| Product | Role | Link |
|---|---|---|
| **Elgato Stream Deck XL + Plus** | the single pane of glass — sounds, mixer, lights | [elgato.com](https://www.elgato.com/stream-deck-xl) |
| **trevligaspel MIDI plugin** | turns Stream Deck buttons into MIDI (see [`stream-deck-scripts/`](stream-deck-scripts/)) | [trevligaspel.se](https://trevligaspel.se/streamdeck/midi/) |
| **Yamaha P-225** | main weighted keyboard | [yamaha.com](https://www.yamaha.com/) |
| **TEControl Breath Controller** | hands-free expression | [tecontrol.se](https://www.tecontrol.se/) |
| **Behringer FCB1010** | MIDI foot controller | [behringer.com](https://www.behringer.com/) |
| **DJ TechTools Midi Fighter** · **Behringer X-Touch Mini** | pad / fader controllers (tested) | [midifighter.com](https://www.midifighter.com/) · [behringer.com](https://www.behringer.com/) |
| **Korg nanoKONTROL2** · **Arturia MiniLab mkII** | compact controllers (tested) | [korg.com](https://www.korg.com/) · [arturia.com](https://www.arturia.com/) |
| **ROLI Seaboard** | expressive MPE keyboard (tested) | [roli.com](https://roli.com/) |

### 🔀 Routing, mixing, monitoring

| Product | Role | Link |
|---|---|---|
| **Bome MIDI Translator Pro** | virtual MIDI ports, message fan-out, keep-alive watchdog | [bome.com](https://www.bome.com/products/miditranslator) |
| **Behringer XR18** | 18-ch digital mixer — scene per song, FOH + IEM | [behringer.com](https://www.behringer.com/product.html?modelCode=P0BI8) |
| **RME Fireface UCX** · **MOTU MicroBook** | audio interfaces (tested) | [rme-audio.de](https://www.rme-audio.de/) · [motu.com](https://motu.com/) |
| **TC-Helicon VoiceLive Touch 2 / VL3X** | vocal harmony & FX | [tc-helicon.com](https://www.tc-helicon.com/) |

### 🎼 Live performance tools

| Product | Role | Link |
|---|---|---|
| **Stage Traxx** | setlist + backing-track player (iOS) | [stagetraxx.com](https://www.stagetraxx.com/) |
| **iReal Pro** | chord charts / play-along | [irealpro.com](https://www.irealpro.com/) |
| **forScore** · **MuseScore** | sheet music / notation | [forscore.co](https://forscore.co/) · [musescore.org](https://musescore.org/) |
| **Amazing Slow Downer** | transcription / slow-down | [ronimusic.com](https://www.ronimusic.com/) |

### 💡 Stage lighting

| Product | Role | Link |
|---|---|---|
| **Tuya / WLED smart lamps** | stage ambiance, driven from the Stream Deck | [wled.io](https://wled.info/) |
| **QLC+** · **Stairville** | DMX / lighting control (tested) | [qlcplus.org](https://www.qlcplus.org/) |

---

## The control logic (what's in this repo)

### [`stream-deck-scripts/`](stream-deck-scripts/) — the button DSL

The trevligaspel plugin runs a small text DSL per button. Examples of what's here:

- **`nav/`** — setlist navigation: `sd_next`, `sd_prev`, `sd_song`, `sd_setlist`, `sd_run_songs`
  → move through the set, one song at a time, hands-free
- **`track/`** — `sd_track1..8`: per-channel mixer strips (VU feedback, fader, select, mute)
  → a physical mixer surface, on the Stream Deck
- **`silence/`** — panic/clean: `sd_main_mute`, `sd_omni_stop`, `sd_clean`
  → instant "everything off" for between-song silence
- **`XR18/sd_talk`** — talkback mic toggle to the mixer
- **`sd_background.txt`** — defines setlists as variables (which songs, in what order)

These are the actual scripts running on stage — readable MIDI logic, no magic.

### Song switching — the ghost-app trick

Stream Deck switches profiles based on which app is "frontmost". So each song gets a tiny
**ghost AppleScript app** (does nothing but quit itself); the Stream Deck profile is bound to
that app's path via `AppIdentifier`. Pressing a song button "launches" the ghost → Stream Deck
flips to that song's page. New song's switcher = copy the template app. Simple, robust, no
plugin dependency.

### Lights from the Stream Deck

A small controller (Python/JS) exposes Tuya/WLED lamps as Stream Deck buttons, so lighting
cues are just more buttons in the same setlist flow. *(Controller code kept private — it holds
device keys — but the integration point is a Stream Deck button like any other.)*

---

## How I work

**Preparing a song.** I build the Ableton rack, dial in the sounds (usually Omnisphere +
Keyscape + a B-3X for organ parts), then create its Stream Deck page and its ghost switcher.
The XR18 gets a matching scene (levels, sends, IEM mix). Everything the song needs is bound to
one entry in the setlist.

**Preparing a set.** Songs are ordered in `sd_background.txt` as a setlist variable. A single
`sd_run_songs` walks the list; `sd_next` / `sd_prev` step through it live. No file browsing on
stage — the surface always shows the current song and the next.

**On stage.** Count-in, play. Between songs: one button loads the next song's sounds, recalls
the mixer scene, and cues the lights. If I need silence fast, `sd_main_mute` / `sd_omni_stop`
kill everything instantly. The laptop screen stays closed.

**After the gig.** A weekly `launchd` job has already snapshotted the whole config into git.
Nothing is manual. If a machine dies, a fresh Mac + a few `git clone`s rebuilds the rig
exactly.

---

## Config-as-code & backup philosophy

Nothing about this rig lives in only one place:

- **Stable device config** (MIDI routing, controller mappings, mixer scenes, SysEx dumps) →
  **git-versioned**. Small, stable, diffable, restorable with a clone.
- **Stream Deck profiles** (churny, rewritten on every edit) → **cloud sync** (delta-friendly)
  + a **weekly git snapshot** for history.
- **Home-automation / analysis scripts** → their own git repos, CI-checked.

A weekly `launchd` job snapshots the live config into git and pushes it; a recovery script
re-materializes everything if a cloud-sync eviction ever blanks the config mid-gig. The result:
**the laptop is disposable** — a fresh machine + a few `git clone`s rebuilds the whole rig.

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
