#!/usr/bin/env python3
"""Install the chosen logo across all favicon/OG image slots."""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "logo_drafts" / "v2-lotus-canang.jpg"
STATIC = ROOT / "themes" / "balikini" / "static"
IMG_DIR = STATIC / "images"
IMG_DIR.mkdir(exist_ok=True)

BG = (7, 12, 9)  # #070c09 deep forest


def crop_center_square(img):
    w, h = img.size
    s = min(w, h)
    return img.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2))


def main():
    src = Image.open(SRC).convert("RGB")
    square = crop_center_square(src)

    # Favicon sizes
    sizes = {
        "favicon-16.png": 16,
        "favicon-32.png": 32,
        "favicon-48.png": 48,
        "favicon-192.png": 192,
        "favicon-512.png": 512,
        "apple-touch-icon.png": 180,
    }
    for name, size in sizes.items():
        out = square.resize((size, size), Image.LANCZOS)
        out.save(STATIC / name, optimize=True)
        print(f"  -> {name} ({size}x{size})")

    # Multi-resolution favicon.ico
    ico_sizes = [(16, 16), (32, 32), (48, 48)]
    ico = square.resize((64, 64), Image.LANCZOS)
    ico.save(STATIC / "favicon.ico", format="ICO", sizes=ico_sizes)
    print(f"  -> favicon.ico (16/32/48)")

    # Header logo — 512x512 square version
    hdr = square.resize((512, 512), Image.LANCZOS)
    hdr.save(IMG_DIR / "logo.png", optimize=True)
    print(f"  -> images/logo.png (512x512)")

    # OG image — 1200x630 with logo on left, brand text baked into background separately
    # Just use square logo centered on 1200x630 dark background
    og = Image.new("RGB", (1200, 630), BG)
    logo_og = square.resize((520, 520), Image.LANCZOS)
    og.paste(logo_og, ((1200 - 520) // 2, (630 - 520) // 2))
    og.save(IMG_DIR / "og-default.jpg", "JPEG", quality=88, optimize=True)
    print(f"  -> images/og-default.jpg (1200x630)")

    print("\nDone. All logo assets installed to themes/balikini/static/")


if __name__ == "__main__":
    main()
