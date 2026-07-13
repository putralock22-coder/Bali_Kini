#!/usr/bin/env python3
"""Refine lotus logo with Balinese accents — v2."""
import os, json, base64, time
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "logo_drafts"
OUT_DIR.mkdir(exist_ok=True)

env_path = ROOT / ".env"
for line in env_path.read_text(encoding="utf-8").splitlines():
    if line.startswith("TOGETHER_API_KEY="):
        os.environ["TOGETHER_API_KEY"] = line.split("=", 1)[1].strip()

API_KEY = os.environ["TOGETHER_API_KEY"]
MODEL = "black-forest-labs/FLUX.1.1-pro"

VARIANTS = [
    {
        # Lotus + canang offering base
        "name": "v2-lotus-canang",
        "prompt": (
            "Minimalist flat vector logo icon on deep forest black background #070c09, "
            "symmetrical composition featuring stylized Balinese lotus flower with three "
            "layered petals in emerald green #22c55e, warm golden sun disk #eab308 rising "
            "behind top petal, small square Balinese canang offering base beneath lotus with "
            "gold detail, extremely clean geometric shapes, no text, no gradients on shapes, "
            "2-color palette emerald and gold only, editorial premium logo design, "
            "distinctly Balinese Hindu symbolism, ios app icon quality, sharp vector edges"
        ),
    },
    {
        # Lotus + penjor bamboo curve
        "name": "v2-lotus-penjor",
        "prompt": (
            "Elegant flat vector logo icon on deep forest black background #070c09, "
            "centered emerald green #22c55e stylized lotus with 5 pointed petals, "
            "warm golden #eab308 rising sun behind central petal, two symmetrical curved "
            "penjor bamboo lines in gold arching over the lotus like a Balinese temple gate, "
            "minimalist Balinese sacred geometry, no text, clean vector shapes, "
            "2-color palette, editorial premium news brand identity, symmetrical composition"
        ),
    },
    {
        # Lotus with omkara/sun mandala center
        "name": "v2-lotus-omkara",
        "prompt": (
            "Sacred minimalist logo icon on deep forest black #070c09 background, "
            "symmetrical Balinese lotus flower with five emerald green #22c55e petals, "
            "centered inside the middle petal a small circular sun mandala in warm gold #eab308 "
            "with 8 subtle rays representing balance and dharma, "
            "flat vector geometric design, extremely clean, no text, no gradients, "
            "2-color palette emerald and gold, sharp edges, distinctly Balinese Hindu sacred, "
            "editorial premium logo, ios app icon quality"
        ),
    },
    {
        # Lotus + kori temple gate silhouette
        "name": "v2-lotus-kori-gate",
        "prompt": (
            "Minimalist flat vector logo icon on deep forest black #070c09 background, "
            "silhouette of stylized Balinese kori agung temple gate arch in emerald green "
            "#22c55e as background frame, inside the gate a warm golden #eab308 lotus flower "
            "with three layered petals and a rising sun disk above, "
            "symmetrical composition, 2-color palette only emerald and gold, "
            "geometric flat vector, no text, no gradients, sharp edges, sacred Balinese design, "
            "editorial premium brand identity, ios app icon quality"
        ),
    },
]


def gen(v):
    payload = {
        "model": MODEL,
        "prompt": v["prompt"],
        "width": 1024,
        "height": 1024,
        "steps": 4,
        "n": 1,
        "response_format": "b64_json",
    }
    req = urllib.request.Request(
        "https://api.together.xyz/v1/images/generations",
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
    out = OUT_DIR / f"{v['name']}.jpg"
    out.write_bytes(img)
    print(f"  -> {out.name} ({len(img)//1024} KB)")


if __name__ == "__main__":
    print(f"Refining lotus with Balinese accents (FLUX.1.1 Pro)...\n")
    for v in VARIANTS:
        print(f"[GEN] {v['name']}")
        try:
            gen(v)
        except Exception as e:
            print(f"  [FAIL] {e}")
        time.sleep(1)
    print("\nDone.")
