# 🎹 How I work

**Preparing a song.** I build the Ableton rack, dial in the sounds (usually Omnisphere +
Keyscape + a B-3X for organ parts), then create its Stream Deck page and its ghost switcher.
The XR18 gets a matching scene (levels, sends, IEM mix). Everything the song needs is bound to
one entry in the setlist.

**Preparing a set.** Songs are ordered in `sd_background.txt` as a setlist variable. A single
`sd_run_songs` walks the list; `sd_next` / `sd_prev` step through it live. No file browsing on
stage — the surface always shows the current song and the next.

**On stage.** Count-in, play. Between songs: one button loads the next song's sounds, recalls
the mixer scene, and cues the lights. If I need silence fast, `sd_main_mute` / `sd_omni_stop`
kill everything instantly. The laptop screen stays closed.

**After the gig.** A weekly `launchd` job has already snapshotted the whole config into git
(see [backup](backup.md)). Nothing is manual. If a machine dies, a fresh Mac + a few
`git clone`s rebuilds the rig exactly.

## Config-as-code & backup

Nothing about this rig lives in only one place:

- **Stable device config** (MIDI routing, controller mappings, mixer scenes, SysEx dumps) →
  **git-versioned**. Small, stable, diffable, restorable with a clone.
- **Stream Deck profiles** (churny, rewritten on every edit) → **cloud sync** (delta-friendly)
  + a **weekly git snapshot** for history.
- **Home-automation / analysis scripts** → their own git repos, CI-checked.

A weekly `launchd` job snapshots the live config into git and pushes it; a recovery script
re-materializes everything if a cloud-sync eviction ever blanks the config mid-gig. The result:
**the laptop is disposable** — a fresh machine + a few `git clone`s rebuilds the whole rig.
