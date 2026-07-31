#!/usr/bin/env python3
"""Export all SVG diagrams in this folder to PNG."""

from __future__ import annotations

from pathlib import Path

import cairosvg

HERE = Path(__file__).resolve().parent


def main() -> None:
    for svg in sorted(HERE.glob("*.svg")):
        png = svg.with_suffix(".png")
        cairosvg.svg2png(url=str(svg), write_to=str(png), output_width=1400)
        print(f"{svg.name} → {png.name}")


if __name__ == "__main__":
    main()
