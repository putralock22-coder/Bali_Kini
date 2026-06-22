#!/usr/bin/env python3
"""Bali Kini — AI Image Generator (FLUX.1 schnell via Together.ai)
Generate fotorealistik illustration for each new article.

Usage:
  python scripts/generate_image.py content/artikel/some-article.md
  python scripts/generate_image.py --all-missing      # process all articles without image
  python scripts/generate_image.py --limit 10         # max N per run
"""
import os, sys, re, json, base64, argparse, time
from pathlib import Path
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parent.parent
IMG_DIR = ROOT / "static" / "images" / "articles"
IMG_DIR.mkdir(parents=True, exist_ok=True)

API_URL = "https://api.together.xyz/v1/images/generations"
MODEL = "black-forest-labs/FLUX.1-schnell"  # serverless, $0.003/img
WIDTH, HEIGHT = 1024, 576  # 16:9 — good for OG image + article hero


def load_env():
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def parse_frontmatter(text):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    if not m:
        return None, text
    fm_raw, body = m.group(1), m.group(2)
    fm = {}
    for line in fm_raw.splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm, body


def write_frontmatter(fm_raw_lines, body, new_image_path):
    """Insert/replace `image:` field in raw frontmatter lines, preserving order."""
    out, replaced = [], False
    for line in fm_raw_lines:
        if line.strip().startswith("image:"):
            out.append(f'image: "{new_image_path}"')
            replaced = True
        else:
            out.append(line)
    if not replaced:
        # insert after title or at start
        inserted = False
        for i, line in enumerate(out):
            if line.strip().startswith("title:"):
                out.insert(i + 1, f'image: "{new_image_path}"')
                inserted = True
                break
        if not inserted:
            out.insert(0, f'image: "{new_image_path}"')
    return "---\n" + "\n".join(out) + "\n---\n" + body


def build_prompt(fm, body):
    """Build a photorealistic news-style prompt from article metadata."""
    title = fm.get("title", "")
    desc = fm.get("description", "") or fm.get("summary", "")
    cats = (fm.get("categories", "") or "").lower()

    # Keyword-based scene hints
    keywords = (title + " " + desc).lower()
    scene_hints = []

    if any(w in keywords for w in ["pantai", "beach", "ombak", "surfing"]):
        scene_hints.append("tropical Balinese beach")
    if any(w in keywords for w in ["pura", "temple", "upacara", "ceremony", "ngaben", "galungan", "nyepi"]):
        scene_hints.append("traditional Balinese temple ceremony")
    if any(w in keywords for w in ["wisatawan", "tourist", "pariwisata", "tourism"]):
        scene_hints.append("tourists exploring Bali")
    if any(w in keywords for w in ["ekonomi", "economy", "inflasi", "rupiah", "bank"]):
        scene_hints.append("Indonesian economic context, modern office or market")
    if any(w in keywords for w in ["cuaca", "hujan", "bmkg", "weather", "rain"]):
        scene_hints.append("dramatic tropical weather over Bali landscape")
    if any(w in keywords for w in ["polisi", "polda", "kpk", "kriminal", "narkoba", "wna"]):
        scene_hints.append("Indonesian law enforcement scene")
    if any(w in keywords for w in ["festival", "pkb", "tari", "seni", "budaya"]):
        scene_hints.append("Balinese cultural festival with traditional costume and dance")
    if any(w in keywords for w in ["sawah", "subak", "petani", "ubud", "tegallalang"]):
        scene_hints.append("Balinese rice terraces, lush green landscape")
    if any(w in keywords for w in ["bandara", "ngurah rai", "pesawat", "airport"]):
        scene_hints.append("Ngurah Rai International Airport in Bali")
    if any(w in keywords for w in ["gubernur", "koster", "pemerintah", "dprd"]):
        scene_hints.append("Indonesian government official press conference")
    if any(w in keywords for w in ["yoga", "meditasi", "wellness", "spa"]):
        scene_hints.append("wellness retreat in Bali, serene atmosphere")

    if not scene_hints:
        scene_hints.append("scenic Bali landscape")

    scene = ", ".join(scene_hints[:2])

    # Short topic phrase (first 80 chars of title without dates)
    topic = re.sub(r"\d{4}-\d{2}-\d{2}", "", title).strip()[:90]

    prompt = (
        f"Photorealistic editorial news photograph: {scene}. "
        f"Subject: {topic}. "
        "Natural lighting, high detail, professional photojournalism style, "
        "sharp focus, depth of field, golden hour, Bali Indonesia, "
        "shot on Canon EOS R5, 35mm lens. No text, no logos, no watermarks."
    )
    return prompt


def generate_image(prompt, api_key, retries=2):
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "width": WIDTH,
        "height": HEIGHT,
        "steps": 4,
        "n": 1,
        "response_format": "b64_json",
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "BaliKini/1.0 (+https://balikini.id)",
            "Accept": "application/json",
        },
    )
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                resp = json.loads(r.read().decode("utf-8"))
            b64 = resp["data"][0]["b64_json"]
            return base64.b64decode(b64)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")[:300]
            print(f"  [HTTP {e.code}] {err_body}", file=sys.stderr)
            if e.code == 429 and attempt < retries:
                time.sleep(10 * (attempt + 1))
                continue
            return None
        except Exception as e:
            print(f"  [ERR] {e}", file=sys.stderr)
            if attempt < retries:
                time.sleep(5)
                continue
            return None


def process_article(md_path: Path, api_key: str, force: bool = False) -> bool:
    text = md_path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    if not m:
        print(f"  [SKIP] No frontmatter: {md_path.name}")
        return False
    fm_raw, body = m.group(1), m.group(2)
    fm_lines = fm_raw.splitlines()
    fm = {}
    for line in fm_lines:
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip().strip('"').strip("'")

    slug = md_path.stem
    existing_img = fm.get("image", "")
    is_ai_image = "/images/articles/" in existing_img

    if not force and is_ai_image:
        print(f"  [SKIP] Already has AI image: {slug}")
        return False

    prompt = build_prompt(fm, body)
    print(f"  [GEN] {slug}")
    print(f"    prompt: {prompt[:120]}...")

    img_bytes = generate_image(prompt, api_key)
    if not img_bytes:
        print(f"  [FAIL] Could not generate image for {slug}")
        return False

    out_path = IMG_DIR / f"{slug}.jpg"
    out_path.write_bytes(img_bytes)
    print(f"    -> saved {out_path.relative_to(ROOT)} ({len(img_bytes)//1024} KB)")

    new_text = write_frontmatter(fm_lines, body, f"/images/articles/{slug}.jpg")
    md_path.write_text(new_text, encoding="utf-8")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*", help="Article markdown files")
    ap.add_argument("--all-missing", action="store_true",
                    help="Process all articles without AI image")
    ap.add_argument("--limit", type=int, default=10,
                    help="Max images per run (default: 10)")
    ap.add_argument("--force", action="store_true",
                    help="Regenerate even if image exists")
    ap.add_argument("--dir", default="content/artikel",
                    help="Article directory (default: content/artikel)")
    args = ap.parse_args()

    load_env()
    api_key = os.environ.get("TOGETHER_API_KEY")
    if not api_key:
        print("ERROR: TOGETHER_API_KEY not set. Add it to .env file.", file=sys.stderr)
        sys.exit(1)

    if args.all_missing:
        article_dir = ROOT / args.dir
        all_md = sorted(article_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
        targets = []
        for md in all_md:
            text = md.read_text(encoding="utf-8")
            fm_m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
            if not fm_m:
                continue
            if "/images/articles/" in fm_m.group(1):
                continue
            targets.append(md)
            if len(targets) >= args.limit:
                break
    else:
        targets = [Path(p) for p in args.paths]

    if not targets:
        print("No articles to process.")
        return

    print(f"Processing {len(targets)} article(s)...")
    ok = 0
    for md in targets:
        if process_article(md, api_key, force=args.force):
            ok += 1
            time.sleep(2)  # gentle rate-limit
    print(f"\nDone: {ok}/{len(targets)} images generated.")


if __name__ == "__main__":
    main()
