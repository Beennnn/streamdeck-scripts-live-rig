# `rig` — bring-up & live monitoring

One command puts the rig on stage; one command watches it while you play.

```bash
cd live-rig
cp bin/rig.example.toml bin/rig.toml   # then edit — set your gig .als, alerts, etc.

bin/rig preflight     # launch Bome → Stream Deck → open the gig set, then verify
bin/rig check         # verify only (no launch) — a fast go/no-go checklist
bin/rig monitor       # watch continuously; alert the moment something dies
bin/rig alert-test    # fire a test alert through every active backend
```

## What it checks

| Check | Level | Why |
|---|---|---|
| Ableton / Stream Deck / Bome running | ❌ fail | the core apps — matched by process, version-agnostic |
| Virtual MIDI ports (`Ableton Loopback`, `Daw2Mackie`, `Mackie2XR18`, `XR182Mackie`) | ❌ fail | if these are gone, nothing routes |
| Optional MIDI gear (keyboard, breath, foot) | ⚠️ warn | absent = just unplugged, not a showstopper |
| Audio interface (`RME Fireface UCX` / `XR18`) | ❌ fail | no interface = no sound |

`preflight` / `check` exit **0** all-green, **1** warnings only, **2** a required check failed —
so you can gate a launcher or a Stream Deck button on the exit code.

## Monitoring & alerts

`monitor` prints a baseline checklist, then alerts **on transitions** (something dies →
alert; it comes back → recovery alert) plus a heartbeat so silence never looks like a hang.
If the rig is already broken when monitoring starts, it alerts immediately.

Pick backends in `rig.toml` (`[monitor].alerts`) or per-run (`--alerts macos,push`):

- **`macos`** — banner + sound via `osascript`. Zero setup; needs the laptop screen.
- **`push`** — HTTP POST to [ntfy.sh](https://ntfy.sh) (stdlib, no install). Set a private
  `[alerts.push].topic`, subscribe to it in the ntfy phone app → buzzes anywhere.
- **`streamdeck`** — emits a MIDI note on a virtual port. Configure a Stream Deck key with
  **MIDI feedback** (note 60, ch 15) to light red on note-on / clear on note-off.
  *(This is why the alert doesn't use the trevligaspel plugin: that plugin is button → MIDI
  only and can't repaint a key from outside. MIDI feedback is the honest inbound path.)*

## Config

`riglib/config.py` holds baked defaults (real process names + virtual ports as of 2026-07).
`rig.toml` (git-ignored) overrides only what differs; `rig.example.toml` is the template.
Requires Python 3.11+ and `mido` (`pip install mido python-rtmidi`).
