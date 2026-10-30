#!/usr/bin/env python3
"""
Generate app icons and DMG background for Lightman.
Creates:
  - assets/app_icon.png      (512x512 PNG with stylized 'L' and light beams)
  - assets/icon.icns         (macOS icon bundle)
  - assets/icon.ico          (Windows icon)
  - assets/dmg_background.png (600x400 with white light beam on dark stage)
"""
from __future__ import annotations
import math
import os
import sys
import subprocess
import shutil
from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
ASSETS_DIR.mkdir(exist_ok=True)


def _make_gradient(draw, width, height, top_color, bottom_color):
    """Draw a vertical gradient."""
    for y in range(height):
        ratio = y / height
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * ratio)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * ratio)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * ratio)
        draw.line([(0, y), (width - 1, y)], fill=(r, g, b, 255))


def create_app_icon() -> Path:
    """Create the application icon PNG (512x512)."""
    from PIL import Image, ImageDraw

    size = 512
    img = Image.new("RGBA", (size, size), (10, 10, 20, 255))
    draw = ImageDraw.Draw(img)

    # Gradient background (deep blue → lighter blue)
    _make_gradient(draw, size, size, (8, 8, 16), (22, 22, 36))

    # Stylized 'L' (cyan/teal)
    l_points = [
        (140, 100), (220, 100), (220, 370),
        (280, 370), (280, 100), (360, 100),
        (360, 420), (140, 420),
    ]
    draw.polygon(l_points, fill=(0, 255, 255, 255))

    # Light beam rays radiating from center-bottom of 'L'
    cx, cy = 256, 260
    for angle in (-25, -15, 0, 15, 25):
        rad = math.radians(angle)
        end_x = cx + math.cos(rad) * 200
        end_y = cy - math.sin(rad) * 200
        draw.line([(cx, cy), (end_x, end_y)], fill=(0, 255, 255, 90), width=8)

    icon_path = ASSETS_DIR / "app_icon.png"
    img.save(icon_path, "PNG")
    print(f"  ✅ Created {icon_path}")
    return icon_path


def png_to_icns(png_path: Path) -> Path:
    """Convert PNG to ICNS using macOS iconutil."""
    icns_path = ASSETS_DIR / "icon.icns"
    iconset = ASSETS_DIR / "icon.iconset"
    iconset.mkdir(exist_ok=True)

    from PIL import Image
    base = Image.open(png_path)
    sizes = [16, 32, 48, 128, 256, 512]
    for s in sizes:
        icon = base.resize((s, s), Image.Resampling.LANCZOS)
        if s <= 256:
            icon.save(iconset / f"icon_{s}x{s}.png")
            icon.save(iconset / f"icon_{s}x{s}@2x.png")
        else:
            icon.save(iconset / f"icon_{s}x{s}.png")

    subprocess.run(
        ["iconutil", "-c", "icns", str(iconset), "-o", str(icns_path)],
        check=True, capture_output=True,
    )
    shutil.rmtree(iconset, ignore_errors=True)
    print(f"  ✅ Created {icns_path}")
    return icns_path


def png_to_ico(png_path: Path) -> Path:
    """Convert PNG to ICO using Pillow."""
    ico_path = ASSETS_DIR / "icon.ico"
    from PIL import Image
    base = Image.open(png_path)
    sizes = [(16, 16), (32, 32), (48, 48), (256, 256)]
    base.save(ico_path, "ICO", sizes=sizes)
    print(f"  ✅ Created {ico_path}")
    return ico_path


def create_dmg_background() -> Path:
    """Create the DMG background image (600x400)."""
    from PIL import Image, ImageDraw, ImageFont

    w, h = 600, 400
    img = Image.new("RGBA", (w, h), (8, 8, 15, 255))
    draw = ImageDraw.Draw(img)

    # Dark gradient stage background
    for y in range(h):
        v = int(8 + (y / h) * 12)
        draw.line([(0, y), (w - 1, y)], fill=(v, v, v + 7, 255))

    # White light beam (tapered searchlight effect)
    beam_cx = 300
    beam_top = 20
    beam_bottom = 380

    for i in range(300):
        t = i / 300.0
        half_width = 80 * (1.0 - t) + 10
        y_top = beam_top + t * (beam_bottom - beam_top - 40)
        y_bottom = beam_top + (t - 0.01) * (beam_bottom - beam_top - 40)
        if y_top > beam_bottom:
            break
        intensity = max(0, 1.0 - t * 0.8)
        r = g = b = int(255 * intensity)
        a = int(150 * intensity)
        pts = [
            (beam_cx - half_width, y_top),
            (beam_cx + half_width, y_top),
            (beam_cx + half_width, y_bottom),
            (beam_cx - half_width, y_bottom),
        ]
        draw.polygon(pts, fill=(r, g, b, a))

    # Stage floor line
    draw.line([(0, 370), (w, 370)], fill=(40, 40, 60, 255), width=3)

    # Equipment silhouettes
    draw.rectangle([80, 330, 120, 370], fill=(20, 20, 30, 200))
    draw.rectangle([480, 330, 520, 370], fill=(20, 20, 30, 200))

    # Lightman text
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
    except Exception:
        font = None

    if font:
        draw.text((220, 30), "LIGHTMAN", fill=(200, 200, 255, 250), font=font)
    else:
        draw.text((220, 30), "LIGHTMAN", fill=(200, 200, 255, 200))

    bg_path = ASSETS_DIR / "dmg_background.png"
    img.save(bg_path, "PNG")
    print(f"  ✅ Created {bg_path}")
    return bg_path


def main():
    print("Generating Lightman assets...")
    png_path = create_app_icon()
    create_dmg_background()

    if sys.platform == "darwin":
        try:
            png_to_icns(png_path)
        except Exception as e:
            print(f"  ⚠️  Could not create icon.icns: {e}")
    else:
        print("  ℹ️  Skipping .icns (non-macOS platform)")

    try:
        png_to_ico(png_path)
    except Exception as e:
        print(f"  ⚠️  Could not create icon.ico: {e}")

    print("Done!")


if __name__ == "__main__":
    main()