#!/usr/bin/env python3
"""gen_profile_sdplus.py - genere Lampes-SDPlus.streamDeckProfile (import double-clic).

Profil demo Stream Deck + (4x2 touches + 4 molettes) pour le plugin com.benlab.lamps :
  touches  : les 8 couleurs (toutes les lampes)
  molette 0: couleur (toutes)          — rotation = defile les 8 couleurs, appui = ON/OFF
  molette 1: intensite (toutes)        — rotation = ±5%/cran, appui = ON/OFF
  molette 2: intensite L1 uniquement   — demontre le ciblage par lampe
  molette 3: intensite L2 uniquement

Regenerer : python3 gen_profile_sdplus.py  puis double-clic sur le .streamDeckProfile.
"""
import json, os, subprocess, uuid, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
# Device = Stream Deck + de Benoit — repris des profils existants
DEVICE = {"Model": "20GBD9901", "UUID": "@(1)[4057/132/A00WA4411KZUFJ]"}

COLORS = {"jaune":(255,210,0),"violet":(150,70,170),"orange":(255,125,0),
          "bleuclair":(130,195,255),"rouge":(230,0,40),"vert":(0,200,80),
          "rose":(255,130,170),"bleu":(0,100,200)}

def svg_color(rgb):
    r,g,b = rgb
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="288" height="288">
<rect width="288" height="288" rx="48" fill="#141414"/>
<circle cx="144" cy="130" r="92" fill="rgb({r},{g},{b})"/>
<circle cx="144" cy="130" r="92" fill="none" stroke="rgba(255,255,255,0.25)" stroke-width="4"/>
</svg>'''

def png(svg, path):
    p = subprocess.run(["rsvg-convert","-w","288","-h","288","-o",path], input=svg.encode())
    if p.returncode: sys.exit("rsvg-convert a echoue pour " + path)

def key_action(title, img, cmd, lamps=None):
    return {
        "ActionID": str(uuid.uuid4()),
        "LinkedTitle": False,
        "Name": "Lampe LED (touche)",
        "Plugin": {"Name": "Lampes LED locales (Tuya / WLED)", "UUID": "com.benlab.lamps",
                   "Version": "1.1.0"},
        "Resources": None,
        "Settings": {"cmd": cmd, "lamps": lamps or []},
        "State": 0,
        "States": [{
            "FontFamily": "", "FontSize": 16, "FontStyle": "", "FontUnderline": False,
            "Image": f"Images/{img}", "OutlineThickness": 2, "ShowTitle": True,
            "Title": "", "TitleAlignment": "bottom", "TitleColor": "#ffffff",  # titre vide -> titre auto du plugin
        }],
        "UUID": "com.benlab.lamps.action",
    }

def dial_action(mode, lamps=None):
    return {
        "ActionID": str(uuid.uuid4()),
        "LinkedTitle": False,
        "Name": "Lampe LED (molette)",
        "Plugin": {"Name": "Lampes LED locales (Tuya / WLED)", "UUID": "com.benlab.lamps",
                   "Version": "1.1.0"},
        "Resources": None,
        "Settings": {"mode": mode, "lamps": lamps or []},
        "State": 0,
        "States": [{}],
        "UUID": "com.benlab.lamps.dial",
    }

def main():
    profile_uuid = str(uuid.uuid4()).upper()
    page_uuid = str(uuid.uuid4()).upper()
    build = os.path.join(HERE, "build-sdplus")
    shutil.rmtree(build, ignore_errors=True)
    root = os.path.join(build, profile_uuid + ".sdProfile")
    pagedir = os.path.join(root, "Profiles", page_uuid)
    imgdir = os.path.join(pagedir, "Images")
    os.makedirs(imgdir)

    keys = {}
    for i, (name, rgb) in enumerate(COLORS.items()):     # 8 couleurs sur la grille 4x2
        png(svg_color(rgb), os.path.join(imgdir, f"col_{name}.png"))
        keys[f"{i % 4},{i // 4}"] = key_action(name, f"col_{name}.png", name)

    dials = {
        "0,0": dial_action("couleur"),                    # toutes
        "1,0": dial_action("intensite"),                  # toutes
        "2,0": dial_action("intensite", ["L1"]),          # ciblage : L1 seule
        "3,0": dial_action("intensite", ["L2"]),          # ciblage : L2 seule
    }

    json.dump({"Controllers": [
                   {"Actions": keys, "Type": "Keypad"},
                   {"Actions": dials, "Type": "Encoder"},
               ], "Name": "Lampes"},
              open(os.path.join(pagedir, "manifest.json"), "w"), indent=1)
    json.dump({"Device": DEVICE, "Name": "Lampes SD+",
               "Pages": {"Current": page_uuid.lower(), "Default": page_uuid.lower(),
                          "Pages": [page_uuid.lower()]},
               "Version": "3.0"},
              open(os.path.join(root, "manifest.json"), "w"), indent=1)

    out = os.path.join(HERE, "Lampes-SDPlus.streamDeckProfile")
    if os.path.exists(out): os.remove(out)
    subprocess.run(["zip","-qr", out, profile_uuid + ".sdProfile"], cwd=build, check=True)
    print("OK ->", out)

if __name__ == "__main__":
    main()
