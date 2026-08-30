# LumiDeck MIDI bridge

Drive your lamps **directly from Ableton, Bome, Logic, or any MIDI source**.

It's just another **frontend** to the LumiDeck engine (same as the Stream Deck
plugin and the CLI): it opens a virtual MIDI port named **`LumiDeck`**, translates
incoming MIDI into OpenLamp State commands, and sends them to the engine's local
API — so the lamps react as instantly as from a key press. The LumiDeck plugin
must be running (it holds the persistent lamp connections).

## Run

```bash
pip install python-rtmidi
python3 lumideck_midi.py
```

In Ableton / Bome / Logic, a new MIDI **output** called `LumiDeck` appears —
route notes / CC / program changes to it.

## Default mapping (edit `mapping.json`)

| MIDI in | Action |
|---|---|
| Notes 60-67 (C3…G3) | 8 colors (yellow, purple, orange, light-blue, red, green, pink, blue) |
| Note 48 / 50 / 52 | OFF / ON / toggle |
| Note 53 / 55 | blackout / restore |
| CC 1 (mod wheel) | brightness 0-100 % |
| CC 2 | white temperature (warm→cold) |
| Program Change 0-N | named scenes/snapshots (`"programs"` list) |
| MIDI clock | `tempo:<bpm>` — pulse lamps on the beat |

`"channel"` (1-16, 0 = all) and `"lamps"` (`[]` = all, else `["L1","L2"]`) are in
`mapping.json`.

## Autostart (optional, macOS)

```bash
cp com.benlab.lumideck-midi.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.benlab.lumideck-midi.plist
```

The bridge then runs in the background and keeps the `LumiDeck` port available.

## Ideas for a live set

- Map a **color per song section** to notes in an Ableton MIDI clip → the lights
  follow the arrangement automatically.
- Send **program changes** at song boundaries → recall a captured scene per song.
- Enable **MIDI clock** → lamps pulse in tempo with the track (`tempo:` animation).
- Use a **fader → CC 1** on your controller for live brightness / house-lights feel.
