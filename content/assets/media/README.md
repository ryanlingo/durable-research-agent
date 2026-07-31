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
