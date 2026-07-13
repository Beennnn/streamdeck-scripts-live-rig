"""Health checks — the source of truth for both preflight and monitor.

Each check returns a Result. Three levels:
  ok    green  — present / running as expected
  warn  yellow — optional thing missing (e.g. keyboard unplugged); not blocking
  fail  red    — required thing missing; the rig is not gig-ready

The checks are cheap (pgrep, an in-process MIDI port enumeration) except audio,
which shells out to system_profiler (~1s) and is therefore rate-limited by the
monitor loop rather than run every cycle.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass

import mido

OK, WARN, FAIL = "ok", "warn", "fail"
_ICON = {OK: "✅", WARN: "⚠️ ", FAIL: "❌"}


@dataclass
class Result:
    key: str        # stable id for state tracking (e.g. "app:Ableton")
    label: str      # human label
    status: str     # ok | warn | fail
    detail: str = ""

    @property
    def icon(self) -> str:
        return _ICON[self.status]

    @property
    def ok(self) -> bool:
        return self.status == OK


def _pgrep(pattern: str) -> bool:
    # -f matches the full command line; pattern is an extended regex.
    return subprocess.run(
        ["pgrep", "-f", pattern],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode == 0


def check_apps(cfg: dict) -> list[Result]:
    out = []
    for label, pattern in cfg["checks"]["apps"].items():
        running = _pgrep(pattern)
        out.append(Result(
            key=f"app:{label}", label=f"{label} lancé",
            status=OK if running else FAIL,
            detail="" if running else "process introuvable",
        ))
    return out


def _midi_inputs() -> list[str]:
    try:
        return list(mido.get_input_names())
    except Exception as exc:  # pragma: no cover - backend init failure
        return [f"__error__:{exc}"]


def check_midi(cfg: dict) -> list[Result]:
    ports = _midi_inputs()
    if ports and ports[0].startswith("__error__:"):
        return [Result("midi:backend", "Backend MIDI", FAIL, ports[0].split(":", 1)[1])]

    def present(name: str) -> bool:
        return any(name.lower() in p.lower() for p in ports)

    out = []
    for name in cfg["checks"]["midi_required"]:
        hit = present(name)
        out.append(Result(
            key=f"midi:{name}", label=f"Port MIDI « {name} »",
            status=OK if hit else FAIL,
            detail="" if hit else "absent",
        ))
    for name in cfg["checks"]["midi_optional"]:
        hit = present(name)
        out.append(Result(
            key=f"midi?:{name}", label=f"Port MIDI « {name} »",
            status=OK if hit else WARN,
            detail="" if hit else "non branché (optionnel)",
        ))
    return out


def check_audio(cfg: dict) -> Result:
    want = cfg["checks"]["audio_interface"]
    try:
        blob = subprocess.run(
            ["system_profiler", "SPAudioDataType"],
            capture_output=True, text=True, timeout=15,
        ).stdout
    except Exception as exc:
        return Result("audio", f"Interface « {want} »", FAIL, f"system_profiler: {exc}")
    hit = want.lower() in blob.lower()
    return Result(
        key="audio", label=f"Interface audio « {want} »",
        status=OK if hit else FAIL,
        detail="" if hit else "non détectée",
    )


def run_all(cfg: dict, with_audio: bool = True) -> list[Result]:
    results = check_apps(cfg) + check_midi(cfg)
    if with_audio:
        results.append(check_audio(cfg))
    return results


def worst(results: list[Result]) -> str:
    if any(r.status == FAIL for r in results):
        return FAIL
    if any(r.status == WARN for r in results):
        return WARN
    return OK
