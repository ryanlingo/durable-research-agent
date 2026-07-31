#!/usr/bin/env python3
"""Record Showcase crash demo (Loom substitute) as video via Playwright.

Usage (UI must already be running on :8765):

    python content/assets/media/record_showcase_demo.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent
BASE = "http://127.0.0.1:8765"
TODAY = date.today().isoformat()
STEM = f"{TODAY}-showcase-crash-demo"


def main() -> int:
    raw_dir = OUT / "_record_raw"
    if raw_dir.exists():
        shutil.rmtree(raw_dir)
    raw_dir.mkdir(parents=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            record_video_dir=str(raw_dir),
            record_video_size={"width": 1440, "height": 900},
        )
        page = context.new_page()
        page.goto(BASE, wait_until="networkidle")
        page.wait_for_timeout(800)

        # Slow pace so crash + recovery are readable without voiceover
        page.select_option("#mode", "showcase")
        page.select_option("#pace", "1.6")
        page.click("#btnStart")

        # Wait for comparison panel (full scripted crash + recovery)
        page.wait_for_selector("#comparison:not(.hidden)", timeout=300_000)
        page.locator("#comparison").scroll_into_view_if_needed()
        page.wait_for_timeout(5000)

        context.close()
        browser.close()

    videos = list(raw_dir.glob("*.webm"))
    if not videos:
        print("No video recorded", file=sys.stderr)
        return 1

    webm = OUT / f"{STEM}.webm"
    webm.write_bytes(videos[0].read_bytes())
    print("wrote", webm)

    mp4 = OUT / f"{STEM}.mp4"
    if shutil.which("ffmpeg"):
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(webm),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(mp4),
            ],
            check=True,
            capture_output=True,
        )
        print("wrote", mp4)
    else:
        print("ffmpeg not found; leaving webm only")

    shutil.rmtree(raw_dir, ignore_errors=True)

    # LINKS.md
    links = OUT / "LINKS.md"
    text = links.read_text(encoding="utf-8") if links.exists() else "# Media links\n\n"
    entry = (
        f"| {TODAY} | Showcase crash demo (video) | P3.2 | "
        f"`content/assets/media/{STEM}.mp4` (or `.webm`) |\n"
    )
    if "Showcase crash demo" not in text:
        if not text.endswith("\n"):
            text += "\n"
        text = text.replace(
            "| | Loom crash demo (90s) | P3.2 | *deferred* |",
            f"| {TODAY} | Loom / screen demo (automated capture) | P3.2 | "
            f"`content/assets/media/{STEM}.mp4` |",
        )
        if "P3.2 |" not in text or "showcase-crash-demo" not in text:
            text += entry
    else:
        text += entry
    links.write_text(text, encoding="utf-8")
    print("updated LINKS.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
