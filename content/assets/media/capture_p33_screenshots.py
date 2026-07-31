#!/usr/bin/env python3
"""P3.3 only: capture Showcase screenshots into this directory."""

from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent
BASE = "http://127.0.0.1:8765"
TODAY = date.today().isoformat()


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1100})
        page.goto(BASE, wait_until="networkidle")

        # 1. Idle dual columns
        idle = OUT / f"{TODAY}-showcase-idle.png"
        page.screenshot(path=str(idle), full_page=True)
        print("wrote", idle.name)

        # Showcase, fast pace so we can grab mid-run + final
        page.select_option("#pace", "0.6")
        page.click("#btnStart")

        # 2. Mid-run: wait until any pipeline looks active
        page.wait_for_function(
            """() => {
              const chips = [...document.querySelectorAll('.status-chip')];
              return chips.some(c => c.textContent && c.textContent.trim() !== 'idle');
            }""",
            timeout=15000,
        )
        page.wait_for_timeout(1200)
        mid = OUT / f"{TODAY}-showcase-mid-run.png"
        page.screenshot(path=str(mid), full_page=True)
        print("wrote", mid.name)

        # 3. Post-crash comparison
        page.wait_for_selector("#comparison:not(.hidden)", timeout=60000)
        page.wait_for_timeout(800)
        # Scroll comparison into view
        page.locator("#comparison").scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        full = OUT / f"{TODAY}-showcase-comparison.png"
        page.screenshot(path=str(full), full_page=True)
        print("wrote", full.name)

        # Crop-ish: also screenshot just comparison region via clip of bounding box
        box = page.locator("#comparison").bounding_box()
        if box:
            crop = OUT / f"{TODAY}-showcase-comparison-panel.png"
            page.screenshot(
                path=str(crop),
                clip={
                    "x": max(0, box["x"] - 8),
                    "y": max(0, box["y"] - 8),
                    "width": box["width"] + 16,
                    "height": box["height"] + 16,
                },
            )
            print("wrote", crop.name)

        browser.close()

    # Update LINKS.md
    links = OUT / "LINKS.md"
    text = links.read_text(encoding="utf-8") if links.exists() else ""
    rows = [
        (f"{TODAY}-showcase-idle.png", "Showcase dual pipelines idle"),
        (f"{TODAY}-showcase-mid-run.png", "Showcase mid-run / crash path"),
        (f"{TODAY}-showcase-comparison.png", "Post-crash full page with savings"),
        (f"{TODAY}-showcase-comparison-panel.png", "Post-crash savings panel only"),
    ]
    for name, label in rows:
        path = f"content/assets/media/{name}"
        line = f"| {TODAY} | {label} | P3.3 | `{path}` |"
        # replace pending lines for that label if present
        if label in text and "pending" in text:
            text = re.sub(
                rf"\|[^\n]*{re.escape(label)}[^\n]*\|",
                line,
                text,
                count=1,
            )
        elif path not in text:
            if not text.endswith("\n"):
                text += "\n"
            text += line + "\n"
    links.write_text(text, encoding="utf-8")
    print("updated LINKS.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
