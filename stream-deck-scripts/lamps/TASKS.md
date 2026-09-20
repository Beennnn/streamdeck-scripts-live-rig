# TASKS — OpenLamp / LumiDeck (source de vérité inter-sessions)

Architecture actuelle (2026-07-04) : famille **OpenLamp**, 1 repo par couche —
[openlamp](https://github.com/openlamp/openlamp) (parapluie) ·
[openlamp-engine](https://github.com/openlamp/openlamp-engine-python) (moteur+démon+CLI) ·
[lumideck](https://github.com/openlamp/lumideck) (Stream Deck) ·
[openlamp-midi](https://github.com/openlamp/openlamp-lib-beatsync) (MIDI musiciens).
Le moteur est extrait dans `engine.py` (hook `on_change` = seul lien vers le
frontal) ; test d'intégration vert post-extraction. Règle : UN hôte à la fois
(plugin OU daemon.py — jamais les deux, port 8377 + créneau unique Tuya).

## À faire

- ◐ **Moteur JS** : porté (engine.js 1128 LOC sur tuyapi, 25 assertions mock vertes ; persisté dans `engine-js/` du Drive + `js/` d'openlamp-engine). ☐ Validation live BLOQUÉE 2026-07-04 11:10 : les DEUX lampes ont disparu du réseau (ni Mango ni box, ARP muet, déauth sans objet — plus associées) → power-cycle physique requis (Benoît), puis re-test : quitter SD, `node engine-js/engine.js`, `curl 127.0.0.1:8377/cmd?c=vert`. Questions ouvertes dans js/README.md (signature session morte via tuyapi, DP24 hex brut, négo 3.5).
- 📌 **Donnée wedge 2026-07-04** : le blocage réseau total a touché les DEUX lampes simultanément (pas seulement L2) → renforce « fragilité partagée du modèle », et l'urgence du watchdog prise niveau 3.
- ✅ **Build Windows via GitHub Actions** (runner windows-latest, artefact .sdPlugin 9 Mo, CI verte 2026-07-04) ; ☐ reste : test sur une vraie machine Windows (appel à testeurs) + chemin de log Windows (~/Library n'existe pas → log silencieux).
- 🚫 **Anti-plantage niveau 3 — watchdog matériel** : BLOQUÉ matériel (pas de Shelly Plug S en stock, confirmé 2026-07-04) → ~12 €/prise à acheter avant un concert ; en attendant, `lamp-doctor.sh` + déauth niveau 1 couvrent le diagnostic/récup à distance (sauf lampe éteinte).
- ☐ **Annonces alpha** (Benoît) : poster ANNONCES-ALPHA.md → Discord Makers /
  r/StreamDeck / communauté WLED.
- ✅ **Maker Console onboarding COMPLET** (2026-07-04 : org BenLab @benlab créée, France, support = issues GitHub, Stripe passé sans connexion). ✅ Fiche produit LumiDeck en DRAFT persisté (2026-07-04) : pack SDK3/6.9 accepté tout vert, DRM auto, type Lighting, Free, médias complets (icône 288 + bannière + 3 visuels, archivés store/), notes de version prêtes (store/RELEASE-NOTES-1.2.0.md), auto-publication DÉSACTIVÉE. ☐ Reste : clic « Submit » par Benoît APRÈS ses tests (puis annonces alpha).
- ☐ **Validation visuelle globale** (Benoît) : passe UX complète du plugin
  (panneau unifié, titres auto, touches Status, molette multi, rainbow greet).

## À surveiller / revalider

- ☐ **Rappel snapshot sur L2** à revalider (lectures radio intermittentes).
- ☐ **Anti-plantage niveau 1 (déauth Mango)** : opérationnel — surveiller son
  efficacité au prochain wedge de L2.
- ☐ **Hypothèse ordre de liste** : L2 en tête depuis 2026-07-04 — sa fragilité
  suit-elle la position ou la lampe ?
- ☐ **setTitle echo guard** : confirmer en pratique (titre user vs titre auto).

## À arbitrer (décisions Benoît)

- 🤔 **WLED+ (`/json/state`)** : reste ~30 lignes DANS l'API du moteur (aucun
  frontal n'en dépend). Repo séparé = artificiel à cette taille. Options :
  (a) garder inline documenté ✅ reco · (b) extraire openlamp-wled · (c) retirer.
- ✅ **Org GitHub `openlamp` créée + 4 repos transférés/renommés** (engine, lumideck, midi, openlamp) + vitrine .github ; liens réécrits, redirections OK (2026-07-04).
- ✅ **publish.sh** créé + testé (Drive → 3 clones + push, exclusions clés locales).

## Verdict perf/fiabilité 2026-07-04 soir (A/B mesuré)
- ✅ Persistant > éphémère sur protocole 3.5 (négo de session ~2-10 s domine l'éphémère) — mesuré, option config `connection` conservée.
- 🔴 PLAFOND MATÉRIEL ATTEINT : plancher sain 17-600 ms, mais pics 2-10 s et sessions qui pourrissent = dégradation du firmware Tuya en ~2 h d'uptime. Plus AUCUN levier logiciel.
- ☐ Court terme : power-cycle des lampes avant chaque session/concert (reset ~2 h de calme) → niveau 3 (prises connectées) l'automatisera.
- ☐ Vérifier mise à jour firmware des lampes dans l'app Smart Life (Benoit, 2 min).
- ☐ **A/B WLED : commander 1 ampoule Athom WLED E27 (~15-20 €)** — le moteur la supporte déjà ; c'est LE chemin scène-grade (protocole honnête, pas de créneau unique, pas de faux acks).

## Migration WLED (décidée 2026-07-04 soir)
- ✅ Driver WLED durci + testé 10/10 contre mock (retry, relecture état réelle, mDNS, verify {v:true}).
- ✅ Autopsie Tuya (8 pathologies) documentée dans engine.py au-dessus de TuyaLamp.
- ✅ Guide de mise en route : store/WLED-SETUP.md.
- ✅ **Tuya renvoyées + 2× Athom WLED commandées** (2026-07-04). Config vidée (plus de churn), clés Tuya sauvegardées (tuya-lamps.json.tuya-backup), template WLED laissé dans la config.
- ☐ À réception : setup (WLED-AP → BEN-MUSIC → IP réservée) + ajout `"type":"wled"` dans la config + test live = 1ère validation WLED sur vrai matériel.
