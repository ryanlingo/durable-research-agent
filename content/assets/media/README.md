# Media

Raster and video exports used by posts, decks, and tutorials.

## Put here

- Loom / screen recordings (or a short `LINKS.md` with URLs if files are too large for git)
- Screenshots (experiment UI, Temporal Web UI Event History)
- GIFs cut from recordings
- Exported diagram PNGs only if they are one-off composites; prefer canonical diagrams in [`../diagrams/`](../diagrams/)

## Naming

```
YYYY-MM-DD-short-slug.ext
```

## Demo video + captions

| File | Role |
|------|------|
| `2026-07-31-showcase-crash-demo.mp4` | Silent automated Showcase (~24s) |
| `2026-07-31-showcase-crash-demo.webm` | Source webm |
| `2026-07-31-showcase-crash-demo.vtt` | Descriptive captions (synced to silent mp4) |
| `2026-07-31-showcase-crash-demo-narration.vtt` | Optional VO track for a 90–120s re-record |
| `watch.html` | Local player with captions enabled |

```bash
# Captioned playback (from this directory)
python -m http.server 8766
# open http://127.0.0.1:8766/watch.html
```

Or load the `.vtt` as a subtitle track in VLC / QuickTime / YouTube after upload.

Narration shot list (if you re-record with mic): [`../loom-crash-demo.md`](../loom-crash-demo.md).

## Capture scripts (optional)

```bash
# requires: pip install playwright && playwright install chromium
python content/assets/media/capture_p33_screenshots.py
python content/assets/media/record_showcase_demo.py
```

Playwright is not a runtime dependency of the lab; only needed to regenerate screenshots/video.

## Git note

Large binaries may not belong in git. Prefer links in `LINKS.md`, or Git LFS later. Keep this folder’s purpose clear either way.
Committed demo assets for this lab currently live in this folder and are listed in `LINKS.md`.
