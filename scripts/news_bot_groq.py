#!/usr/bin/env python3
"""Bali Kini news bot (Groq). Runs on the VPS.

RSS -> pick useful topics -> fetch source -> Groq rewrite (ID) -> Groq translate (EN)
-> source photo (fallback: FLUX) -> markdown -> hugo build check -> git commit/push.

Usage:
  python3 scripts/news_bot_groq.py --limit 2
  python3 scripts/news_bot_groq.py --limit 1 --no-push   # write + build, no commit
  python3 scripts/news_bot_groq.py --limit 1 --dry-run   # print only
"""
import argparse, io, json, os, re, subprocess, sys, tempfile, time, unicodedata
from datetime import datetime, timezone
from pathlib import Path

import feedparser
import requests
from bs4 import BeautifulSoup

try:
    import fcntl
except ImportError:  # Windows dev machine
    fcntl = None

ROOT = Path(__file__).resolve().parent.parent
ID_DIR = ROOT / "content" / "artikel"
EN_DIR = ROOT / "content" / "en" / "artikel"
IMG_DIR = ROOT / "static" / "images" / "articles"
SEEN_FILE = ROOT / "logs" / "bot_seen.json"
LOCK_FILE = Path(tempfile.gettempdir()) / "balikini-bot.lock"

FEEDS = [
    ("Antara Bali", "https://bali.antaranews.com/rss/terkini.xml"),
    ("Tribun Bali", "https://bali.tribunnews.com/rss"),
]
UA = "Mozilla/5.0 (compatible; BalikiniBot/1.0; +https://balikini.id)"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
FALLBACK_MODEL = "llama-3.1-8b-instant"
CATEGORIES = ["Pariwisata", "Ekonomi", "Budaya", "Berita", "Sosial", "Lingkungan", "Olahraga", "Hukum"]
CAT_EN = {"Pariwisata": "Tourism", "Ekonomi": "Economy", "Budaya": "Culture", "Berita": "News",
          "Sosial": "Society", "Lingkungan": "Environment", "Olahraga": "Sports", "Hukum": "Law"}
STOP = set("yang di dan ke untuk dengan dari ini itu pada akan bali juga atau oleh sebagai dalam tak "
           "tidak ada para telah sudah saat hari tahun 2026 kini bagi usai jadi".split())


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def load_env():
    for p in (Path("/etc/balikini/env"), ROOT / ".env"):
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())


def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def slugify(s, n=70):
    s = re.sub(r"[^a-z0-9]+", "-", strip_accents(s.lower())).strip("-")
    return s[:n].rstrip("-") or "artikel"


def toks(s):
    s = re.sub(r"[^a-z0-9 ]+", " ", strip_accents(s.lower()))
    return {w for w in s.split() if w not in STOP and len(w) > 2}


def similar(a, b):
    if not a or not b:
        return False
    inter = len(a & b)
    return inter / len(a | b) >= 0.4 or inter / min(len(a), len(b)) >= 0.7


def existing_titles():
    out = []
    for md in ID_DIR.glob("*.md"):
        try:
            head = md.read_text(encoding="utf-8", errors="replace")[:600]
        except OSError:
            continue
        m = re.search(r'^title:\s*"?(.*?)"?\s*$', head, re.M)
        if m:
            out.append(toks(m.group(1)))
    return out


def load_seen():
    try:
        return json.loads(SEEN_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_seen(seen):
    SEEN_FILE.parent.mkdir(exist_ok=True)
    items = sorted(seen.items(), key=lambda kv: kv[1])[-2000:]
    SEEN_FILE.write_text(json.dumps(dict(items), indent=0), encoding="utf-8")


def fetch_candidates(seen):
    cands = []
    for publisher, url in FEEDS:
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=20)
            feed = feedparser.parse(r.content)
        except Exception as e:
            log(f"feed fail {publisher}: {e}")
            continue
        for e in feed.entries[:25]:
            link = e.get("link", "").strip()
            if not link or link in seen:
                continue
            pub = e.get("published_parsed")
            if pub and (time.time() - time.mktime(pub)) > 3 * 86400:
                continue
            cands.append({"title": e.get("title", "").strip(), "link": link, "publisher": publisher})
        log(f"{publisher}: {len(feed.entries)} entries")
    return cands


# ---------- Groq ----------
def groq_json(system, user, max_tokens=3500):
    key = os.environ["GROQ_API_KEY"]
    model = MODEL
    for attempt in range(5):
        try:
            r = requests.post(
                GROQ_URL,
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"model": model, "temperature": 0.3, "max_tokens": max_tokens,
                      "response_format": {"type": "json_object"},
                      "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]},
                timeout=120,
            )
        except requests.RequestException as e:
            log(f"groq network error: {e}")
            time.sleep(5)
            continue
        if r.status_code == 429:
            wait = min(60, float(r.headers.get("retry-after", 10 * (attempt + 1))))
            log(f"groq 429, wait {wait:.0f}s (attempt {attempt + 1})")
            if attempt >= 2:
                model = FALLBACK_MODEL
            time.sleep(wait)
            continue
        if r.status_code >= 400:
            log(f"groq {r.status_code}: {r.text[:200]}")
            time.sleep(5)
            continue
        try:
            return json.loads(r.json()["choices"][0]["message"]["content"])
        except (ValueError, KeyError, IndexError):
            log("groq returned invalid JSON")
    return None


def pick_topics(cands, n):
    listing = "\n".join(f"{i}. [{c['publisher']}] {c['title']}" for i, c in enumerate(cands))
    data = groq_json(
        "Kamu editor senior portal berita Bali Kini. Dari daftar judul, pilih artikel yang paling bermanfaat dan "
        "informatif bagi warga, wisatawan, dan pelaku usaha di Bali (kebijakan, ekonomi, pariwisata, budaya, "
        "lingkungan, layanan publik, event). Hindari kriminal receh, gosip, olahraga di luar Bali, berita yang bukan "
        "tentang Bali, dan topik kembar. Variasikan topik. Jawab JSON: {\"picks\": [nomor, ...]} urut dari terbaik.",
        f"Pilih {n * 3} nomor terbaik dari daftar ini:\n{listing}", max_tokens=300)
    picks = []
    if data and isinstance(data.get("picks"), list):
        picks = [i for i in data["picks"] if isinstance(i, int) and 0 <= i < len(cands)]
    return [cands[i] for i in dict.fromkeys(picks)] or cands


# ---------- source page ----------
BOILER = ("baca juga", "baca selengkapnya", "pewarta", "editor:", "copyright", "follow", "simak berita",
          "klik di sini", "advertisement", "scroll")


def fetch_source(url):
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=25)
        r.raise_for_status()
    except Exception as e:
        log(f"source fail: {e}")
        return None
    soup = BeautifulSoup(r.text, "lxml")
    og = soup.find("meta", property="og:image")
    paras = []
    for p in soup.find_all("p"):
        t = p.get_text(" ", strip=True)
        if len(t) > 60 and not any(b in t.lower() for b in BOILER):
            paras.append(t)
    text = "\n\n".join(dict.fromkeys(paras))[:7000]
    return {"text": text, "image": og["content"].strip() if og and og.get("content") else ""}


def number_set(s):
    return {re.sub(r"[.,]", "", n) for n in re.findall(r"\d[\d.,]*\d|\d", s)}


def numbers_grounded(body, source):
    src = number_set(source)
    unknown = [n for n in number_set(body) if len(n) > 1 and n not in src and n not in ("2025", "2026")]
    return len(unknown) <= 2, unknown


SYS_ID = (
    "Kamu jurnalis senior Bali Kini (balikini.id). Susun artikel orisinal Bahasa Indonesia dari laporan sumber.\n"
    "ATURAN KETAT:\n"
    "- Pakai HANYA fakta, angka, nama, dan kutipan yang ada di teks sumber. Dilarang mengarang data atau kutipan.\n"
    "- Jangan menyalin kalimat sumber; tulis ulang dengan susunan sendiri.\n"
    "- Struktur: paragraf pembuka 5W1H (60-80 kata), 3-4 subjudul H2, lalu H2 terakhir 'Apa Artinya bagi Bali' "
    "berisi analisis singkat yang jelas ditandai sebagai analisis redaksi (bukan fakta baru).\n"
    "- Panjang 450-800 kata sesuai kedalaman materi sumber; jangan menambah isi demi panjang.\n"
    "- Gaya netral, tanpa clickbait. Tanpa judul H1 di body.\n"
    "Keluaran JSON valid dengan kunci: title (maks 70 karakter), description (140-160 karakter), "
    f"category (salah satu: {', '.join(CATEGORIES)}), tags (array 4-6 string huruf kecil), body (markdown)."
)
SYS_EN = (
    "You are a professional news translator for Bali Kini. Translate the Indonesian article into natural, "
    "neutral news English. Keep every fact and number exactly; keep the markdown structure and headings. "
    "Output valid JSON with keys: title (max 70 chars), description (140-160 chars), tags (array of 4-6 "
    "lowercase English strings), body (markdown, no H1)."
)


def write_article_id(src, text):
    user = f"Judul sumber: {src['title']}\nPenerbit: {src['publisher']}\n\nTeks sumber:\n{text}"
    for attempt in range(2):
        data = groq_json(SYS_ID, user)
        if not data:
            return None
        body = (data.get("body") or "").strip()
        body = re.sub(r"^#\s+.*\n", "", body)
        if not data.get("title") or not data.get("description") or len(body.split()) < 250:
            log("ID draft too short/incomplete")
            continue
        ok, unknown = numbers_grounded(body, text + src["title"])
        if not ok:
            log(f"ungrounded numbers {unknown[:5]}, retry")
            user += f"\n\nPERINGATAN: angka {unknown[:5]} tidak ada di sumber. Hapus atau jangan pakai angka itu."
            continue
        cat = data.get("category") if data.get("category") in CATEGORIES else "Berita"
        tags = [str(t).lower() for t in (data.get("tags") or [])][:6] or ["bali"]
        return {"title": data["title"].strip(), "description": data["description"].strip(),
                "category": cat, "tags": tags, "body": body}
    return None


def translate_en(art):
    payload = json.dumps({"title": art["title"], "description": art["description"],
                          "tags": art["tags"], "body": art["body"]}, ensure_ascii=False)
    data = groq_json(SYS_EN, payload)
    if not data or not data.get("title") or len((data.get("body") or "").split()) < 200:
        return None
    return {"title": data["title"].strip(), "description": (data.get("description") or "").strip(),
            "tags": [str(t).lower() for t in (data.get("tags") or art["tags"])][:6],
            "body": re.sub(r"^#\s+.*\n", "", data["body"].strip())}


# ---------- image ----------
def download_image(url, slug, referer):
    if not url or "logo" in url.lower():
        return None
    try:
        r = requests.get(url, headers={"User-Agent": UA, "Referer": referer}, timeout=25)
    except requests.RequestException:
        return None
    ct = r.headers.get("content-type", "").split(";")[0].lower()
    if r.status_code != 200 or not ct.startswith("image/") or not 15_000 <= len(r.content) <= 8_000_000:
        return None
    data, ext = r.content, {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}.get(ct)
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(data)).convert("RGB")
        if im.width > 1200:
            im = im.resize((1200, int(im.height * 1200 / im.width)))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=82, optimize=True)
        data, ext = buf.getvalue(), "jpg"
    except Exception:
        pass
    if not ext:
        return None
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    (IMG_DIR / f"{slug}.{ext}").write_bytes(data)
    return f"/images/articles/{slug}.{ext}"


# ---------- markdown ----------
def make_md(meta, body, lang, source):
    q = lambda v: json.dumps(v, ensure_ascii=False)
    fm = ["---", f"title: {q(meta['title'])}", f"date: {meta['date']}", f"lastmod: {meta['date']}",
          f"description: {q(meta['description'])}", f"categories: {q([meta['category']])}",
          f"tags: {q(meta['tags'])}",
          f"author: {q('Redaksi Bali Kini' if lang == 'id' else 'Bali Kini Editorial')}",
          'generator: "balikini-news-bot"']
    if meta.get("image"):
        fm += [f"image: {q(meta['image'])}", f"image_credit: {q(meta['image_credit'])}"]
    fm += ["sources:", f"  - title: {q(source['title'])}", f"    url: {q(source['link'])}",
           f"    publisher: {q(source['publisher'])}", "---", ""]
    if lang == "id":
        foot = f"\n\n*Artikel ini disusun redaksi Bali Kini berdasarkan laporan [{source['publisher']}]({source['link']}).*\n"
    else:
        foot = f"\n\n*Compiled by the Bali Kini editorial team from reporting by [{source['publisher']}]({source['link']}).*\n"
    return "\n".join(fm) + body.strip() + foot


def unique_path(directory, slug, date):
    p = directory / f"{slug}-{date}.md"
    i = 2
    while p.exists():
        p = directory / f"{slug}-{date}-{i}.md"
        i += 1
    return p


# ---------- git / hugo ----------
def run(cmd, check=True, env=None):
    return subprocess.run(cmd, cwd=ROOT, check=check, env=env, text=True, capture_output=True)


def hugo_ok():
    r = run(["hugo", "--minify", "--quiet"], check=False)
    if r.returncode != 0:
        log(f"hugo build failed: {r.stderr[-400:]}")
    return r.returncode == 0


def commit_and_push(files, titles):
    env = dict(os.environ, GIT_SSH_COMMAND="ssh -i /root/.ssh/balikini_deploy -o IdentitiesOnly=yes "
                                            "-o StrictHostKeyChecking=accept-new")
    run(["git", "add", "--", *[str(f.relative_to(ROOT)) for f in files], "logs/bot_seen.json"])
    msg = f"[bot] {datetime.now(timezone.utc):%Y-%m-%d} - {len(titles)} artikel: " + "; ".join(t[:45] for t in titles)
    run(["git", "commit", "-m", msg])
    run(["git", "pull", "--no-rebase", "-X", "ours", "origin", "main"], env=env, check=False)
    r = run(["git", "push", "origin", "HEAD:main"], env=env, check=False)
    if r.returncode != 0:
        log(f"push failed: {r.stderr[-300:]}")
        return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=2)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-push", action="store_true")
    args = ap.parse_args()

    load_env()
    if not os.environ.get("GROQ_API_KEY"):
        sys.exit("GROQ_API_KEY missing")

    lock = open(LOCK_FILE, "w")
    if fcntl:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            log("another run is active, exiting")
            return

    seen = load_seen()
    titles_now = existing_titles()
    cands = []
    for c in fetch_candidates(seen):
        t = toks(c["title"])
        if any(similar(t, old) for old in titles_now):
            seen[c["link"]] = datetime.now(timezone.utc).isoformat()
            continue
        cands.append(c)
    log(f"{len(cands)} fresh candidates")
    if not cands:
        return

    picks = pick_topics(cands[:40], args.limit)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    written, titles, done = [], [], 0

    for src in picks[: args.limit * 3]:
        if done >= args.limit:
            break
        seen[src["link"]] = datetime.now(timezone.utc).isoformat()
        t = toks(src["title"])
        if any(similar(t, old) for old in titles_now):
            continue
        log(f"processing: {src['title']}")
        page = fetch_source(src["link"])
        if not page or len(page["text"]) < 400:
            log("source text too thin, skip")
            continue
        art = write_article_id(src, page["text"])
        if not art:
            continue
        en = translate_en(art)
        if not en:
            log("translation failed, skip")
            continue
        if args.dry_run:
            log(f"DRY: {art['title']} | {len(art['body'].split())} words\n{art['body'][:300]}")
            done += 1
            continue

        slug = slugify(art["title"])
        image = download_image(page["image"], f"{slug}-{today}", src["link"])
        credit = f"Foto: {src['publisher']}" if image else ""
        id_path = unique_path(ID_DIR, slug, today)
        en_path = unique_path(EN_DIR, slugify(en["title"]), today)
        meta_id = dict(art, date=today, image=image, image_credit=credit)
        meta_en = dict(en, date=today, category=CAT_EN.get(art["category"], "News"),
                       image=image, image_credit=credit.replace("Foto:", "Photo:"))
        ID_DIR.mkdir(parents=True, exist_ok=True)
        EN_DIR.mkdir(parents=True, exist_ok=True)
        id_path.write_text(make_md(meta_id, art["body"], "id", src), encoding="utf-8")
        en_path.write_text(make_md(meta_en, en["body"], "en", src), encoding="utf-8")
        files = [id_path, en_path] + ([IMG_DIR / Path(image).name] if image else [])
        if not image:  # fallback: AI illustration (FLUX) for both languages
            for p in (id_path, en_path):
                subprocess.run([sys.executable, str(ROOT / "scripts" / "generate_image.py"), str(p)],
                               cwd=ROOT, capture_output=True, text=True)
            files += list(IMG_DIR.glob(f"{id_path.stem}*")) + list(IMG_DIR.glob(f"{en_path.stem}*"))
        written += files
        titles.append(art["title"])
        titles_now.append(toks(art["title"]))
        done += 1
        log(f"written: {id_path.name} ({'source photo' if image else 'AI photo'})")
        time.sleep(20)  # stay under Groq TPM

    save_seen(seen)
    if args.dry_run or not written:
        return
    if not hugo_ok():
        for f in written:
            f.unlink(missing_ok=True)
        log("aborted: build failed, files removed")
        return
    if args.no_push:
        log("no-push: files written and build OK")
        return
    log("pushed" if commit_and_push(written, titles) else "push FAILED (articles stay local)")


if __name__ == "__main__":
    main()
