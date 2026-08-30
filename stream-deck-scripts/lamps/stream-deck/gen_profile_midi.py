#!/usr/bin/env python3
"""gen_profile_midi.py - an XL dashboard EQUIVALENT, but routed through the Stream
Deck MIDI plugin (se.trevligaspel.midi) instead of the direct LumiDeck plugin.

Each key sends the note/CC MIDI that, routed to the virtual "LumiDeck" port (opened
by the midi bridge), triggers the SAME action. This is the Stream Deck -> MIDI ->
bridge -> engine path (one-way, no visual feedback) — handy to drive from the same
MIDI flow as Ableton, or without the direct plugin.

Prereq: the MIDI bridge runs (midi-bridge/lumideck_midi.py), and each key's MIDI
plugin has "LumiDeck" as its output (smo field). We pre-fill it; if Stream Deck does
not keep the output, pick it once in a key's panel.

Channel = group (see the bridge mapping.json). Here channel 1 = all lamps.
Regenerate: python3 gen_profile_midi.py  then double-click the .streamDeckProfile.
"""
import json, os, subprocess, uuid, shutil, sys, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
DEVICE = {"Model": "20GAT9901", "UUID": "@(1)[4057/108/CL13L2A01061]"}
MIDI_OUT = "LumiDeck"     # bridge virtual port (smo field of the MIDI plugin)
CHANNEL = 1               # MIDI channel = target group (1 = all)

# reuse the direct generator visuals (same icons)
_spec = importlib.util.spec_from_file_location("gp", os.path.join(HERE, "gen_profile.py"))
gp = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(gp)
COLORS, PALIERS = gp.COLORS, gp.PALIERS
PAL = dict(PALIERS)     # PALIERS is a list of tuples -> dict for lookup

# MIDI note per discrete action (inverse of the bridge mapping.json)
NOTE = {"jaune":60,"violet":61,"orange":62,"bleuclair":63,"rouge":64,"vert":65,
        "rose":66,"bleu":67,"off":48,"on":50,"toggle":52,"blackout":53,"restore":55,
        "music":56,"animstop":57,"flash":58,"cycle":59}

def midi_xt(cmd):
    """OLS command -> trevligaspel MIDI script [(press){...}]"""
    if cmd in NOTE:
        return "[(press){noteon:%d,%d,127}]\n" % (CHANNEL, NOTE[cmd])
    if cmd in PAL:
        return "[(press){cc:%d,1,%d}]\n" % (CHANNEL, round(PAL[cmd] / 100 * 127))
    if cmd.startswith("bri:"):
        pct = int(cmd.split(":")[1])
        return "[(press){cc:%d,1,%d}]\n" % (CHANNEL, round(pct / 100 * 127))
    if cmd.startswith("set:"):     # advanced: color (note) + brightness (cc)
        _, c, p = cmd.split(":")
        return "[(press){noteon:%d,%d,127}{cc:%d,1,%d}]\n" % (
            CHANNEL, NOTE.get(c, 67), CHANNEL, round(int(p) / 100 * 127))
    if cmd == "mode:music":
        return "[(press){noteon:%d,56,127}]\n" % CHANNEL
    return None

def script_action(title, img, cmd):
    xt = midi_xt(cmd)
    if xt is None:
        return None
    return {
        "ActionID": str(uuid.uuid4()),
        "LinkedTitle": False,
        "Name": "Script",
        "Plugin": {"Name": "MIDI", "UUID": "se.trevligaspel.midi", "Version": "3.5.1"},
        "Resources": None,
        "Settings": {
            "a1": None, "el": False, "i9": False, "i9h": "", "lf": False,
            "mi": [], "mo": [], "pds": [], "pv": "3.5.1", "sds": True,
            "sf": None, "sff": "", "shf": False, "sm": "", "smi": "",
            "smo": MIDI_OUT, "spds": "Select", "spw": "", "ss": True,
            "ssm": False, "xt": xt,
        },
        "State": 0,
        "States": [{
            "FontFamily": "", "FontSize": 16, "FontStyle": "", "FontUnderline": False,
            "Image": f"Images/{img}", "OutlineThickness": 2, "ShowTitle": True,
            "Title": "", "TitleAlignment": "bottom", "TitleColor": "#ffffff",
        }],
        "UUID": "se.trevligaspel.midi.script",
    }

def main():
    profile_uuid = str(uuid.uuid4()).upper()
    page_uuid = str(uuid.uuid4()).upper()
    build = os.path.join(HERE, "build-midi")
    shutil.rmtree(build, ignore_errors=True)
    root = os.path.join(build, profile_uuid + ".sdProfile")
    pagedir = os.path.join(root, "Profiles", page_uuid)
    imgdir = os.path.join(pagedir, "Images")
    os.makedirs(imgdir)

    actions = {}
    for x, (name, rgb) in enumerate(COLORS.items()):           # row 0: colors
        gp.png(gp.svg_color(rgb), os.path.join(imgdir, f"col_{name}.png"))
        actions[f"{x},0"] = script_action(name, f"col_{name}.png", name)
    for x, (name, pct) in enumerate(PALIERS):                  # row 1: brightness presets
        gp.png(gp.svg_palier(pct), os.path.join(imgdir, f"pal_{name}.png"))
        actions[f"{x},1"] = script_action(name, f"pal_{name}.png", name)
    gp.png(gp.svg_power(True), os.path.join(imgdir, "on.png"))
    actions["6,1"] = script_action("ON", "on.png", "on")
    gp.png(gp.svg_power(False), os.path.join(imgdir, "off.png"))
    actions["7,1"] = script_action("OFF", "off.png", "off")
    # row 2: extras covered by MIDI (music + animations + advanced demo)
    extras = [("music", "mode:music", gp.svg_mode("music")),
              ("flash", "flash", gp.svg_avance(COLORS["bleuclair"], 100)),
              ("cycle", "cycle", gp.svg_avance(COLORS["vert"], 100)),
              ("stop", "animstop", gp.svg_power(False))]
    for x, (label, cmd, svg) in enumerate(extras):
        gp.png(svg, os.path.join(imgdir, f"x_{label}.png"))
        actions[f"{x},2"] = script_action(label, f"x_{label}.png", cmd)
    for x, (cname, pct) in [(5, ("rouge", 100)), (6, ("bleu", 30))]:
        gp.png(gp.svg_avance(COLORS[cname], pct), os.path.join(imgdir, f"set_{cname}{pct}.png"))
        actions[f"{x},2"] = script_action(f"{cname} {pct}%", f"set_{cname}{pct}.png",
                                          f"set:{cname}:{pct}")

    actions = {k: v for k, v in actions.items() if v}          # drop the non-mappable
    json.dump({"Controllers": [{"Actions": actions, "Type": "Keypad"}], "Name": "Lampes MIDI"},
              open(os.path.join(pagedir, "manifest.json"), "w"), indent=1)
    json.dump({"Device": DEVICE, "Name": "Lampes scene (MIDI)",
               "Pages": {"Current": page_uuid.lower(), "Default": page_uuid.lower(),
                          "Pages": [page_uuid.lower()]}, "Version": "3.0"},
              open(os.path.join(root, "manifest.json"), "w"), indent=1)

    out = os.path.join(HERE, "Lampes-scene-MIDI.streamDeckProfile")
    if os.path.exists(out): os.remove(out)
    subprocess.run(["zip", "-qr", out, profile_uuid + ".sdProfile"], cwd=build, check=True)
    print("OK ->", out)

if __name__ == "__main__":
    main()
