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

import json
import subprocess
import time
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

    def to_dict(self) -> dict:
        return {"key": self.key, "label": self.label,
                "status": self.status, "detail": self.detail}


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
    # An optional entry may be a single port name OR a list of alternatives
    # (e.g. P-225 / Digital Piano — the same keyboard under two driver names).
    # The group is satisfied if ANY alternative is present.
    for entry in cfg["checks"]["midi_optional"]:
        alts = entry if isinstance(entry, list) else [entry]
        label = " / ".join(alts)
        found = next((a for a in alts if present(a)), None)
        out.append(Result(
            key=f"midi?:{alts[0]}", label=f"Clavier « {label} »" if len(alts) > 1 else f"Port MIDI « {label} »",
            status=OK if found else WARN,
            detail=f"détecté : {found}" if found else "non branché (optionnel)",
        ))
    return out


def check_bome_iphone(cfg: dict) -> Result:
    """Detect the Bome Network ↔ iPhone link via an ESTABLISHED TCP connection on
    Bome Network's port (37000). The iPhone runs Bome Network and connects here."""
    port = cfg["checks"].get("bome_network_port", 37000)
    host = str(cfg["checks"].get("iphone_host", "")).strip()
    try:
        out = subprocess.run(
            ["lsof", "-nP", f"-iTCP:{port}", "-sTCP:ESTABLISHED"],
            capture_output=True, text=True, timeout=6,
        ).stdout
    except Exception as exc:
        return Result("net:iphone", "Bome Network ↔ iPhone", FAIL, f"lsof: {exc}")

    lines = [l for l in out.splitlines() if "ESTABLISHED" in l]
    if host:
        lines = [l for l in lines if host in l]
    if not lines:
        return Result("net:iphone", "Bome Network ↔ iPhone", FAIL,
                      "aucune connexion (iPhone déconnecté ?)")
    # NAME column looks like "192.168.1.10:37000->192.168.1.20:52345 (ESTABLISHED)"
    peer = ""
    for tok in lines[0].split():
        if "->" in tok:
            peer = tok.split("->", 1)[1]
            break
    return Result("net:iphone", "Bome Network ↔ iPhone", OK,
                  f"connecté{f' ({peer})' if peer else ''}")


# system_profiler is slow (~1s); cache its JSON so audio + default-output checks
# (and a polling dashboard) share one call instead of shelling out repeatedly.
_profile_cache: dict = {"ts": 0.0, "data": None}
_PROFILE_TTL = 10.0


def _audio_items() -> list[dict]:
    now = time.time()
    if _profile_cache["data"] is None or now - _profile_cache["ts"] > _PROFILE_TTL:
        try:
            out = subprocess.run(
                ["system_profiler", "SPAudioDataType", "-json"],
                capture_output=True, text=True, timeout=15,
            ).stdout
            _profile_cache["data"] = json.loads(out)
        except Exception:
            _profile_cache["data"] = {}
        _profile_cache["ts"] = now
    data = _profile_cache["data"] or {}
    return [it for top in data.get("SPAudioDataType", []) for it in top.get("_items", [])]


def check_audio(cfg: dict) -> Result:
    want = cfg["checks"]["audio_interface"]
    names = [it.get("_name", "") for it in _audio_items()]
    hit = any(want.lower() in n.lower() for n in names)
    return Result(
        key="audio", label=f"Interface audio « {want} »",
        status=OK if hit else FAIL,
        detail="" if hit else "non détectée",
    )


def check_default_output(cfg: dict) -> Result:
    """The macOS default sound output must be the Mac itself (built-in), not an
    external / AirPlay / conferencing device."""
    want = cfg["checks"].get("default_output_match", "MacBook")
    name = None
    for it in _audio_items():
        if it.get("coreaudio_default_audio_output_device") == "spaudio_yes":
            name = it.get("_name", "")
            break
    if name is None:
        return Result("sys:output", "Sortie son par défaut (Mac)", WARN, "indéterminée")
    ok = want.lower() in name.lower()
    return Result(
        key="sys:output", label="Sortie son par défaut (Mac)",
        status=OK if ok else FAIL,
        detail=f"actuellement : {name}" if not ok else name,
    )


# PPP:Modem entries here are serial gadgets (ToneX pedal, Seeed boards), not VPNs —
# a VPN is a *connected* service that isn't one of those serial modems.
def check_vpn(cfg: dict) -> Result:
    try:
        out = subprocess.run(["scutil", "--nc", "list"],
                             capture_output=True, text=True, timeout=5).stdout
    except Exception as exc:
        return Result("sys:vpn", "VPN inactif", WARN, f"scutil: {exc}")
    active = [l for l in out.splitlines()
              if "(Connected)" in l and "[PPP:Modem]" not in l]
    if not active:
        return Result("sys:vpn", "VPN inactif", OK, "")
    name = ""
    if '"' in active[0]:
        name = active[0].split('"')[1]
    return Result("sys:vpn", "VPN inactif", FAIL, f"VPN actif : {name}".rstrip(" :"))


def run_all(cfg: dict, with_audio: bool = True) -> list[Result]:
    results = check_apps(cfg) + check_midi(cfg)
    results += [check_bome_iphone(cfg), check_vpn(cfg)]
    if with_audio:
        results += [check_default_output(cfg), check_audio(cfg)]
    return results


def worst(results: list[Result]) -> str:
    if any(r.status == FAIL for r in results):
        return FAIL
    if any(r.status == WARN for r in results):
        return WARN
    return OK
