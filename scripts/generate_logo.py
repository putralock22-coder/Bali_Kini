#!/usr/bin/env python3
"""Generate Bali Kini logo variants using FLUX.1.1 Pro on Together.ai."""
import os, sys, json, base64, time
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "logo_drafts"
OUT_DIR.mkdir(exist_ok=True)

API_URL = "https://api.together.xyz/v1/images/generations"
MODEL = "black-forest-labs/FLUX.1.1-pro"

# Load API key from .env
env_path = ROOT / ".env"
for line in env_path.read_text(encoding="utf-8").splitlines():
    if line.startswith("TOGETHER_API_KEY="):
        os.environ["TOGETHER_API_KEY"] = line.split("=", 1)[1].strip()

API_KEY = os.environ["TOGETHER_API_KEY"]

VARIANTS = [
    {
        "name": "icon-terrace-sun",
        "size": (1024, 1024),
        "prompt": (
            "Minimalist flat vector logo icon design, single circular composition, "
            "warm gold sun disk rising above three curved emerald green rice terrace lines, "
            "colors strictly: emerald green #22c55e and warm gold #eab308 on deep forest black #070c09 background, "
            "extremely clean geometric shapes, 2-color palette only, no gradients, no shadows, no text, "
            "editorial premium news brand identity, symmetrical, ios app icon quality, "
            "vector illustration style, sharp edges, professional logo design"
        ),
    },
    {
        "name": "icon-b-monogram",
        "size": (1024, 1024),
        "prompt": (
            "Modern minimalist app icon, rounded square with gradient from emerald green #22c55e "
            "to warm gold #eab308, centered white geometric bold letter B in Plus Jakarta Sans style, "
            "premium editorial brand identity, ios app icon quality, "
            "flat vector, no shadows, no decorative elements, extremely clean, "
            "readable at 16x16 pixels, professional logo design"
        ),
    },
    {
        "name": "icon-wave-sun-circle",
        "size": (1024, 1024),
        "prompt": (
            "Ultra minimal circular logo icon, deep forest black #070c09 circle background, "
            "inside: small warm gold #eab308 sun disk in upper area, "
            "one smooth curved emerald green #22c55e wave line beneath, "
            "extremely simple 2-shape composition, "
            "flat vector, geometric, no text, no gradients, no drop shadows, "
            "ios app icon quality, professional news brand identity"
        ),
    },
    {
        "name": "icon-lotus-sunrise",
        "size": (1024, 1024),
        "prompt": (
            "Abstract minimalist logo icon combining stylized lotus petal silhouette "
            "with rising sun disk, warm gold #eab308 sun above three emerald green #22c55e "
            "curved petal shapes, deep forest black #070c09 background, "
            "flat vector geometric design, no text, 2 color palette, "
            "editorial premium brand identity representing Balinese daily wisdom, "
            "symmetrical composition, ios app icon quality, clean sharp edges"
        ),
    },
    {
        "name": "wordmark-full",
        "size": (1280, 720),
        "prompt": (
            "Editorial newspaper masthead logo showing text 'BALI KINI' in bold clean "
            "sans-serif typography white color, small warm gold #eab308 circle dot above "
            "the letter i, thin emerald green #22c55e horizontal underline beneath, "
            "deep forest black #070c09 background, "
            "flat vector newspaper masthead design, extremely clean typography, "
            "premium editorial news brand identity, horizontal layout"
        ),
    },
]


def gen(variant):
    payload = {
        "model": MODEL,
        "prompt": variant["prompt"],
        "width": variant["size"][0],
        "height": variant["size"][1],
        "steps": 4,
        "n": 1,
        "response_format": "b64_json",
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "BaliKini/1.0",
        },
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        resp = json.loads(r.read().decode())
    img = base64.b64decode(resp["data"][0]["b64_json"])
    out = OUT_DIR / f"{variant['name']}.jpg"
    out.write_bytes(img)
    print(f"  -> {out.relative_to(ROOT)} ({len(img)//1024} KB)")
    return out


if __name__ == "__main__":
    print(f"Generating {len(VARIANTS)} logo variants with FLUX.1.1 Pro...")
    for v in VARIANTS:
        print(f"[GEN] {v['name']}")
        try:
            gen(v)
        except Exception as e:
            print(f"  [FAIL] {e}")
        time.sleep(1)
    print(f"\nDone. Check: {OUT_DIR}")
