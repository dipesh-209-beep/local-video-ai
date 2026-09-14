#!/usr/bin/env python3
"""
make_diagrams.py

Generates one full-screen 1080x1920 procedural diagram per beat
(beat01.png, beat02.png, ...) from a STUDENT/TEACHER beat-script JSON.
Labels are taken from each beat's on_screen_caption, so any script works
without code changes.

Usage:
    python3 make_diagrams.py script.json out_dir/ [--width 1080] [--height 1920]

Requires: Pillow.
"""

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def main():
    ap = argparse.ArgumentParser(description="Generate per-beat diagram PNGs from a beat script")
    ap.add_argument("script", help="beat-script JSON (with beats[].on_screen_caption)")
    ap.add_argument("out_dir", help="directory to write beatNN.png files")
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--height", type=int, default=1920)
    ap.add_argument("--font", default="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    args = ap.parse_args()

    data = json.loads(Path(args.script).read_text())
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    W, H = args.width, args.height
    cap_font = ImageFont.truetype(args.font, round(H * 0.05))
    sub_font = ImageFont.truetype(args.font, round(H * 0.025))

    for beat in data["beats"]:
        n = beat["beat_number"]
        label = beat["on_screen_caption"]

        img = Image.new("RGB", (W, H), (16, 18, 32))
        d = ImageDraw.Draw(img)
        for y in range(H):
            shade = 16 + int(8 * y / H)
            d.line([(0, y), (W, y)], fill=(shade, shade + 2, shade + 16))
        d.ellipse((round(W * 0.03), round(H * 0.57), round(W * 0.97), H), fill=(26, 28, 46))
        d.ellipse((0, round(H * 0.42), round(W * 0.39), round(H * 0.68)), fill=(24, 26, 42))
        d.rectangle(
            (round(W * 0.04), round(H * 0.13), round(W * 0.96), round(H * 0.47)),
            fill=(10, 12, 20), outline=(40, 44, 64), width=4,
        )

        bbox = d.textbbox((0, 0), label, font=cap_font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        d.text(
            ((W - tw) / 2 - bbox[0], round(H * 0.23)),
            label, font=cap_font, fill=(240, 242, 255),
        )
        d.text(
            ((W - round(W * 0.44)) / 2, round(H * 0.32)),
            f"beat  {n:02d}", font=sub_font, fill=(120, 128, 160),
        )

        png = out / f"beat{n:02d}.png"
        img.save(png)
        print(png)


if __name__ == "__main__":
    main()