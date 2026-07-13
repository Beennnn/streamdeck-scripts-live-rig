"""Load the rig configuration.

Resolution order for the config file:
  1. $RIG_CONF if set
  2. bin/rig.toml           (your real config — git-ignored, may hold a private ntfy topic)
  3. bin/rig.example.toml   (committed template — used as-is if you never copy it)

Whatever file is found is merged over DEFAULTS below, so a partial rig.toml
only needs to override what differs from the template. Python 3.11+ reads TOML
natively via tomllib (no dependency).
"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path

BIN_DIR = Path(__file__).resolve().parent.parent

# Baked defaults derived from the actual machine state on 2026-07-13 (real
# process names, real virtual MIDI ports). Every value is overridable in rig.toml.
DEFAULTS: dict = {
    "set": {
        # Two Ableton installs exist ("Suite" and "Suite 3"); the gig one is Suite 3.
        "ableton_app": "/Applications/Ableton Live 12 Suite 3.app",
        # The only live (non-Trash) .als found. CONFIRM this is your gig set.
        "project": "/Users/benoitbesson/Documents/Bome MIDI Translator/Presets/Ableton Live MGO Rig 1.00.als",
        "open_after_launch": True,
    },
    "launch": {
        # Order: Bome (MIDI translation/fan-out) up before the set; Stream Deck anytime.
        # NB: the virtual ports (Ableton Loopback, Daw2Mackie, …) are provided by the
        # macOS IAC Driver, which is already enabled — so they exist at boot regardless
        # of app launch order. Bome still handles the translation layer on top of them.
        "apps": [
            "/Applications/Bome MIDI Translator Pro.app",
            "/Applications/Elgato Stream Deck.app",
        ],
        "settle_seconds": 2,   # grace after an app launches before polling readiness
    },
    "checks": {
        # label -> substring matched against the full process command line (pgrep -f).
        # Version-agnostic on purpose (matches "Suite 3" or a future "Suite 4").
        "apps": {
            "Ableton": "Ableton Live.*/MacOS/Live",
            "Stream Deck": "Elgato Stream Deck.app/Contents/MacOS/Stream Deck",
            "Bome": "MIDITranslatorPro",
        },
        # MIDI input ports that MUST be present for the rig to route (substring match).
        "midi_required": [
            "Ableton Loopback",
            "Daw2Mackie",
            "Mackie2XR18",
            "XR182Mackie",
        ],
        # Present only when the hardware is plugged in — warn, don't fail.
        "midi_optional": [
            "Breath Controller",   # TEControl
            "MIDI Friend",
            "P-225",               # Yamaha keyboard (name varies by driver)
            "Digital Piano",
        ],
        # Audio interface expected active. Currently RME Fireface UCX; XR18 on gig days.
        "audio_interface": "RME Fireface UCX",
    },
    "monitor": {
        "interval": 5,        # seconds between fast checks (apps + MIDI)
        "audio_every": 6,     # run the slow audio check once every N cycles
        "alerts": ["macos"],  # active backends: macos, push, streamdeck
        "recovery_alerts": True,
    },
    "alerts": {
        "push": {
            "server": "https://ntfy.sh",
            "topic": "",       # set a PRIVATE topic, e.g. "benoit-rig-9d3f", to enable
            "priority": "high",
        },
        "streamdeck": {
            # A note sent to this virtual OUTPUT port lights a MIDI-feedback button.
            "port": "Ableton Loopback",
            "channel": 15,     # 1-16 (kept off the musical channels)
            "note": 60,
        },
    },
}


def _deep_merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def config_path() -> Path | None:
    env = os.environ.get("RIG_CONF")
    if env:
        return Path(env)
    for name in ("rig.toml", "rig.example.toml"):
        p = BIN_DIR / name
        if p.exists():
            return p
    return None


def load() -> dict:
    path = config_path()
    if path and path.exists():
        with path.open("rb") as fh:
            user = tomllib.load(fh)
        return _deep_merge(DEFAULTS, user)
    return DEFAULTS
