#!/usr/bin/env python3
"""gen_profile.py - genere Lampes-scene.streamDeckProfile (import double-clic).

Profil Stream Deck XL (8x4) pour piloter les 2 lampes Tuya via lamp.py :
  rangee 0 : 8 couleurs (ordre = COLORS de lamp.py, aligne sur le mapping MIDI 0-7)
  rangee 1 : 6 paliers d'intensite + ON + OFF
Chaque touche = plugin OSA Script (com.gabrielperales.osascript) qui fait
`do shell script "python3 lamp.py <action> &"` — lance en arriere-plan pour que
la touche reste reactive (le scan MAC de secours peut prendre plusieurs secondes).

Regenerer apres modif : python3 gen_profile.py  puis double-clic sur le .streamDeckProfile.
"""
import json, os, subprocess, uuid, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
# python Framework (celui qui a tinytuya) — do shell script a un PATH minimal,
# donc chemin absolu obligatoire
PYTHON = "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3"
# lamp.py vit un cran au-dessus de ce generateur (dossier Drive des scripts Stream Deck)
LAMP = os.path.join(os.path.dirname(HERE), "lamp.py")
# Device = Stream Deck XL de Benoit (8x4) — repris des profils existants
DEVICE = {"Model": "20GAT9901", "UUID": "@(1)[4057/108/CL13L2A01061]"}

COLORS = {"jaune":(255,210,0),"violet":(150,70,170),"orange":(255,125,0),
          "bleuclair":(130,195,255),"rouge":(230,0,40),"vert":(0,200,80),
          "rose":(255,130,170),"bleu":(0,100,200)}
PALIERS = [("lueur",1),("veilleuse",10),("tamise",30),("moyen",55),("fort",80),("max",100)]

def svg_color(rgb):
    r,g,b = rgb
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="288" height="288">
<rect width="288" height="288" rx="48" fill="#141414"/>
<circle cx="144" cy="130" r="92" fill="rgb({r},{g},{b})"/>
<circle cx="144" cy="130" r="92" fill="none" stroke="rgba(255,255,255,0.25)" stroke-width="4"/>
</svg>'''

def svg_palier(pct):
    # disque blanc dont la taille + opacite suivent l'intensite
    r = 30 + pct * 0.62
    op = 0.25 + pct * 0.0075
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="288" height="288">
<rect width="288" height="288" rx="48" fill="#141414"/>
<circle cx="144" cy="130" r="{r:.0f}" fill="rgba(255,240,200,{op:.2f})"/>
<text x="144" y="142" font-family="Helvetica" font-size="52" font-weight="bold"
 fill="#ffffff" text-anchor="middle">{pct}</text>
</svg>'''

def svg_mode(mode):
    # pictos des 4 modes de l'app Tuya
    inner = {
        "white":  '<circle cx="144" cy="130" r="86" fill="#f5eeda"/>',
        "colour": '<path d="M144 44 A86 86 0 0 1 230 130 L144 130 Z" fill="#e60028"/>'
                  '<path d="M230 130 A86 86 0 0 1 144 216 L144 130 Z" fill="#00c850"/>'
                  '<path d="M144 216 A86 86 0 0 1 58 130 L144 130 Z" fill="#0064c8"/>'
                  '<path d="M58 130 A86 86 0 0 1 144 44 L144 130 Z" fill="#ffd200"/>',
        "scene":  '<path d="M144 48 L166 108 L230 108 L178 146 L198 208 L144 170 '
                  'L90 208 L110 146 L58 108 L122 108 Z" fill="#b48cff"/>',
        "music":  '<path d="M118 190 L118 74 L206 56 L206 172" fill="none" '
                  'stroke="#7dd8ff" stroke-width="16" stroke-linejoin="round"/>'
                  '<circle cx="96" cy="190" r="26" fill="#7dd8ff"/>'
                  '<circle cx="184" cy="172" r="26" fill="#7dd8ff"/>',
    }[mode]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="288" height="288">
<rect width="288" height="288" rx="48" fill="#141414"/>{inner}</svg>'''

def svg_avance(rgb, pct):
    # mode avance : pastille couleur + % incruste
    r,g,b = rgb
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="288" height="288">
<rect width="288" height="288" rx="48" fill="#141414"/>
<circle cx="144" cy="130" r="92" fill="rgb({r},{g},{b})"/>
<text x="144" y="150" font-family="Helvetica" font-size="60" font-weight="bold"
 fill="#141414" text-anchor="middle">{pct}</text>
</svg>'''

def svg_power(on):
    col = "#2ecc40" if on else "#e0301e"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="288" height="288">
<rect width="288" height="288" rx="48" fill="#141414"/>
<circle cx="144" cy="130" r="80" fill="none" stroke="{col}" stroke-width="18"
 stroke-linecap="round" stroke-dasharray="440" stroke-dashoffset="70"
 transform="rotate(115 144 130)"/>
<line x1="144" y1="40" x2="144" y2="120" stroke="{col}" stroke-width="18" stroke-linecap="round"/>
</svg>'''

def png(svg, path):
    p = subprocess.run(["rsvg-convert","-w","288","-h","288","-o",path], input=svg.encode())
    if p.returncode: sys.exit("rsvg-convert a echoue pour " + path)

# True = action du plugin dedie com.benlab.lamps (connexions persistantes, reponse
# immediate, feedback ✓/⚠). False = fallback OSA Script (lance lamp.py, ~4 s).
USE_PLUGIN = True

def _states(title, img):
    return [{
        "FontFamily": "", "FontSize": 16, "FontStyle": "", "FontUnderline": False,
        "Image": f"Images/{img}", "OutlineThickness": 2, "ShowTitle": True,
        "Title": "", "TitleAlignment": "bottom", "TitleColor": "#ffffff",  # titre vide -> titre auto du plugin
    }]

def action(title, img, cmd):
    if USE_PLUGIN:
        return {
            "ActionID": str(uuid.uuid4()),
            "LinkedTitle": False,
            "Name": "Lampe Tuya",
            "Plugin": {"Name": "Lampes Tuya", "UUID": "com.benlab.lamps", "Version": "1.0.0"},
            "Resources": None,
            "Settings": {"cmd": cmd},
            "State": 0,
            "States": _states(title, img),
            "UUID": "com.benlab.lamps.action",
        }
    return {
        "ActionID": str(uuid.uuid4()),
        "LinkedTitle": False,
        "Name": "OSAScript",
        "Plugin": {"Name": "OSA Script", "UUID": "com.gabrielperales.osascript", "Version": "1.0.0"},
        "Resources": None,
        "Settings": {
            "language": "AppleScript",
            # LAMP quote (le chemin Drive contient des espaces : "Elgato Stream Deck")
            "scriptText": f'do shell script "{PYTHON} \'{LAMP}\' {cmd} >/dev/null 2>&1 &"',
        },
        "State": 0,
        "States": _states(title, img),
        "UUID": "com.gabrielperales.osascript.action",
    }

def main():
    profile_uuid = str(uuid.uuid4()).upper()
    page_uuid = str(uuid.uuid4()).upper()
    build = os.path.join(HERE, "build")
    shutil.rmtree(build, ignore_errors=True)
    root = os.path.join(build, profile_uuid + ".sdProfile")
    pagedir = os.path.join(root, "Profiles", page_uuid)
    imgdir = os.path.join(pagedir, "Images")
    os.makedirs(imgdir)

    actions = {}
    for x, (name, rgb) in enumerate(COLORS.items()):
        png(svg_color(rgb), os.path.join(imgdir, f"col_{name}.png"))
        actions[f"{x},0"] = action(name, f"col_{name}.png", name)
    for x, (name, pct) in enumerate(PALIERS):
        png(svg_palier(pct), os.path.join(imgdir, f"pal_{name}.png"))
        actions[f"{x},1"] = action(name, f"pal_{name}.png", name)
    png(svg_power(True), os.path.join(imgdir, "on.png"))
    actions["6,1"] = action("ON", "on.png", "on")
    png(svg_power(False), os.path.join(imgdir, "off.png"))
    actions["7,1"] = action("OFF", "off.png", "off")
    # rangee 2 : les 4 modes de l'app Tuya + 2 demos du mode avance (couleur+intensite)
    for x, mode in enumerate(["white", "colour", "scene", "music"]):
        png(svg_mode(mode), os.path.join(imgdir, f"mode_{mode}.png"))
        actions[f"{x},2"] = action(mode, f"mode_{mode}.png", "mode:" + mode)
    for x, (cname, pct) in [(5, ("rouge", 100)), (6, ("bleu", 30))]:
        png(svg_avance(COLORS[cname], pct), os.path.join(imgdir, f"set_{cname}{pct}.png"))
        actions[f"{x},2"] = action(f"{cname} {pct}%", f"set_{cname}{pct}.png",
                                   f"set:{cname}:{pct}")

    # "Type": "Keypad" obligatoire — sans lui Stream Deck ignore toutes les touches a l'import
    json.dump({"Controllers": [{"Actions": actions, "Type": "Keypad"}], "Name": "Lampes"},
              open(os.path.join(pagedir, "manifest.json"), "w"), indent=1)
    json.dump({"Device": DEVICE, "Name": "Lampes scene",
               "Pages": {"Current": page_uuid.lower(), "Default": page_uuid.lower(),
                          "Pages": [page_uuid.lower()]},
               "Version": "3.0"},
              open(os.path.join(root, "manifest.json"), "w"), indent=1)

    out = os.path.join(HERE, "Lampes-scene.streamDeckProfile")
    if os.path.exists(out): os.remove(out)
    subprocess.run(["zip","-qr", out, profile_uuid + ".sdProfile"], cwd=build, check=True)
    print("OK ->", out)

if __name__ == "__main__":
    main()
