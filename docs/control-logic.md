# 🎚️ Control logic

How one button press drives sounds, mixer and lights at once.

## The button DSL — [`../stream-deck-scripts/`](../stream-deck-scripts/)

The trevligaspel plugin runs a small text DSL per Stream Deck button. What's in this repo:

- **`nav/`** — setlist navigation: `sd_next`, `sd_prev`, `sd_song`, `sd_setlist`, `sd_run_songs`
  → move through the set, one song at a time, hands-free
- **`track/`** — `sd_track1..8`: per-channel mixer strips (VU feedback, fader, select, mute)
  → a physical mixer surface, on the Stream Deck
- **`silence/`** — panic/clean: `sd_main_mute`, `sd_omni_stop`, `sd_clean`
  → instant "everything off" for between-song silence
- **`XR18/sd_talk`** — talkback mic toggle to the mixer
- **`sd_background.txt`** — defines setlists as variables (which songs, in what order)

These are the actual scripts running on stage — readable MIDI logic, no magic.

## Song switching — the ghost-app trick

Stream Deck switches profiles based on which app is "frontmost". So each song gets a tiny
**ghost AppleScript app** (does nothing but quit itself); the profile is bound to that app's
path via `AppIdentifier`. Pressing a song button "launches" the ghost → Stream Deck flips to
that song's page. New song's switcher = copy the template app. Simple, robust, no plugin
dependency.

## The fan-out

The button emits MIDI. **Bome MIDI Translator** receives it and fans it out to every
destination at once — Ableton (song select), the XR18 (scene recall), the lamp controller
(lighting cue). One gesture, three systems.

## Lights from the Stream Deck

A small controller (Python/JS) exposes Tuya/WLED lamps as Stream Deck buttons, so lighting
cues are just more buttons in the same setlist flow. *(Controller code kept private — it holds
device keys — but the integration point is a Stream Deck button like any other.)*
