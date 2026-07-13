#!/usr/bin/env python3
"""Notify Make.com webhook after publishing new articles.
Sends article metadata → Make.com routes to Facebook Page (+ later: IG, Twitter).

Usage:
  python scripts/notify_socmed.py content/artikel/some-article.md
  python scripts/notify_socmed.py --latest       # process most recent article
  python scripts/notify_socmed.py --since HEAD~1 # process all articles from last commit
"""
import os, sys, re, json, argparse, subprocess, io
from pathlib import Path
import urllib.request
import urllib.error

# Force UTF-8 stdout on Windows so emoji-containing captions don't crash prints
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, io.UnsupportedOperation):
    pass

ROOT = Path(__file__).resolve().parent.parent
SITE_URL = "https://balikini.id"
WEBHOOK_URL = "https://hook.us2.make.com/t7sbcmfq73x787w1p4ae38sijjeao8vd"


def load_env():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def parse_article(md_path: Path):
    text = md_path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    if not m:
        return None
    fm_raw = m.group(1)
    fm = {}
    for line in fm_raw.splitlines():
        if ":" in line and not line.startswith(" ") and not line.startswith("-"):
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm


_URL_CACHE = None


def _load_hugo_urls():
    """Run `hugo list all` once and cache path→permalink map."""
    global _URL_CACHE
    if _URL_CACHE is not None:
        return _URL_CACHE
    _URL_CACHE = {}
    try:
        import csv
        out = subprocess.check_output(
            ["hugo", "list", "all"], cwd=ROOT, text=True, encoding="utf-8"
        )
        reader = csv.reader(out.splitlines())
        for row in reader:
            if len(row) < 8:
                continue
            path, _slug, _title, _date, _exp, _pub, _draft, permalink = row[:8]
            # normalize path separator to match Path.as_posix()
            path_norm = path.replace("\\", "/")
            _URL_CACHE[path_norm] = permalink
    except Exception as e:
        print(f"  [WARN] Could not run 'hugo list all': {e}", file=sys.stderr)
    return _URL_CACHE


def build_url(md_path: Path, is_en: bool = False) -> str:
    urls = _load_hugo_urls()
    # Resolve md_path to absolute, then relativize to ROOT
    md_abs = md_path if md_path.is_absolute() else (ROOT / md_path).resolve()
    try:
        rel = md_abs.relative_to(ROOT).as_posix()
    except ValueError:
        rel = str(md_path).replace("\\", "/")
    if rel in urls:
        return urls[rel]
    # Fallback: filename-based (only if hugo not available)
    slug = md_path.stem
    return f"{SITE_URL}/en/article/{slug}/" if is_en else f"{SITE_URL}/artikel/{slug}/"


def build_payload(md_path: Path):
    fm = parse_article(md_path)
    if not fm:
        return None
    is_en = "content/en/" in str(md_path).replace("\\", "/")
    title = fm.get("title", "").strip()
    desc = fm.get("description", "").strip()
    image = fm.get("image", "").strip()
    category = fm.get("categories", "").strip("[]").split(",")[0].strip().strip('"').strip("'")
    tags = fm.get("tags", "").strip("[]")

    # Full URL for image if relative
    if image.startswith("/"):
        image = f"{SITE_URL}{image}"
    if not image:
        image = f"{SITE_URL}/images/og-default.jpg"

    article_url = build_url(md_path, is_en)

    # Build social-optimized caption
    hashtags = "#BaliKini #Bali #BeritaBali"
    if category:
        hashtags += f" #{category.replace(' ', '')}"
    if is_en:
        caption = f"📰 {title}\n\n{desc}\n\n🔗 Read more: {article_url}\n\n{hashtags} #BaliNews"
    else:
        caption = f"📰 {title}\n\n{desc}\n\n🔗 Baca lengkap: {article_url}\n\n{hashtags}"

    return {
        "title": title,
        "description": desc,
        "image_url": image,
        "article_url": article_url,
        "category": category,
        "tags": tags,
        "caption": caption,
        "lang": "en" if is_en else "id",
    }


def post_webhook(payload):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        WEBHOOK_URL,
        data=data,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "BaliKini/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode("utf-8", errors="replace")
            return r.status, body
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")[:200]
    except Exception as e:
        return 0, str(e)


def get_articles_from_commit(ref: str):
    """List new/modified article markdowns from a git ref."""
    try:
        out = subprocess.check_output(
            ["git", "diff", "--name-only", "--diff-filter=A", ref, "HEAD"],
            cwd=ROOT,
            text=True,
        )
    except subprocess.CalledProcessError:
        return []
    paths = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("content/artikel/") or line.startswith("content/en/artikel/"):
            if line.endswith(".md"):
                paths.append(ROOT / line)
    return paths


def get_latest_article():
    articles = sorted((ROOT / "content" / "artikel").glob("*.md"),
                      key=lambda p: p.stat().st_mtime, reverse=True)
    return articles[0] if articles else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--latest", action="store_true", help="Post the most recent article")
    ap.add_argument("--since", help="Post articles added since git ref (e.g. HEAD~1)")
    ap.add_argument("--dry-run", action="store_true", help="Print payload only")
    ap.add_argument("--limit", type=int, default=5, help="Max posts per run")
    args = ap.parse_args()

    load_env()

    if args.latest:
        latest = get_latest_article()
        targets = [latest] if latest else []
    elif args.since:
        targets = get_articles_from_commit(args.since)
    else:
        targets = [Path(p) for p in args.paths]

    targets = targets[: args.limit]

    if not targets:
        print("No articles to post.")
        return

    print(f"Posting {len(targets)} article(s) to Make.com webhook...\n")
    for md in targets:
        if not md.exists():
            print(f"  [SKIP] {md} does not exist")
            continue
        payload = build_payload(md)
        if not payload:
            print(f"  [SKIP] {md.name} — no frontmatter")
            continue

        print(f"[POST] {md.name}")
        print(f"    -> {payload['article_url']}")

        if args.dry_run:
            print(f"    caption preview: {payload['caption'][:100]}...")
            continue

        status, body = post_webhook(payload)
        marker = "OK" if status == 200 else "FAIL"
        print(f"    [{marker} {status}] {body[:80]}")

    print("\nDone.")


if __name__ == "__main__":
    main()
