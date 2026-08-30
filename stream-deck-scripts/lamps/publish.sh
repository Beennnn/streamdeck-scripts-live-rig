#!/bin/sh
# publish.sh — sync the Drive folder (source of truth) into the 4 OpenLamp repo
# clones and push. Prevents the "edited on Drive, forgot to publish" drift.
# Usage: ./publish.sh [commit message]
set -e
DRIVE="$(cd "$(dirname "$0")" && pwd)"
SCRATCH="${OPENLAMP_CLONES:-/private/tmp/claude-501/-Users-benoitbesson-dev-mirador/6eee57a2-0680-4c08-89eb-017646ec88a6/scratchpad}"
MSG="${1:-chore: sync from Drive source of truth}"

sync_one() {  # sync_one <repo-dir> <src>:<dst> ...
  name="$1"; repo="$SCRATCH/$1"; shift
  [ -d "$repo/.git" ] || { echo "!! clone manquant: $repo (git clone d'abord)"; return 1; }
  for pair in "$@"; do
    src="${pair%%:*}"; dst="${pair#*:}"
    rsync -a --exclude tuya-lamps.json --exclude __pycache__ --exclude '*.bak*' \
      "$DRIVE/$src" "$repo/$dst"
  done
  ( cd "$repo" && git add -A \
    && { git diff --cached --quiet && echo "   $name: rien de neuf" \
         || { git commit -q -m "$MSG

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" && git push -q && echo "   $name: poussé"; }; } )
}

echo "publish: Drive -> repos OpenLamp"
sync_one openlamp-engine \
  sd-plugin/engine.py:engine.py sd-plugin/daemon.py:daemon.py \
  sd-plugin/run-headless.sh:run-headless.sh lamp.py:lamp.py \
  sd-plugin/com.benlab.lumideck-daemon.plist:com.benlab.lumideck-daemon.plist
sync_one lumideck-repo \
  sd-plugin/engine.py:streamdeck/engine.py sd-plugin/plugin.py:streamdeck/plugin.py \
  sd-plugin/daemon.py:streamdeck/daemon.py sd-plugin/manifest.json:streamdeck/manifest.json \
  sd-plugin/ui/:streamdeck/ui/ sd-plugin/test_integration.py:streamdeck/test_integration.py \
  sd-plugin/build-package.sh:streamdeck/build-package.sh sd-plugin/install.sh:streamdeck/install.sh \
  sd-plugin/run-headless.sh:streamdeck/run-headless.sh \
  stream-deck/gen_profile.py:streamdeck/profiles/gen_profile.py \
  stream-deck/gen_profile_sdplus.py:streamdeck/profiles/gen_profile_sdplus.py \
  stream-deck/gen_profile_midi.py:streamdeck/profiles/gen_profile_midi.py
sync_one lumideck-midi \
  midi-bridge/lumideck_midi.py:lumideck_midi.py midi-bridge/MIDI-PROTOCOL.md:MIDI-PROTOCOL.md \
  midi-bridge/ENCAPSULATION.md:ENCAPSULATION.md \
  midi-bridge/com.benlab.lumideck-midi.plist:com.benlab.lumideck-midi.plist
echo "publish: fini"
