#!/usr/bin/env python3
"""Bali Kini — Daily News Aggregator
Fetches RSS from Bali news sources and generates a Hugo markdown article.
"""
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
import re, os, sys

def fetch_rss(url):
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; BalikiniBot/1.0; +https://balikini.id)'
        })
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read().decode('utf-8', errors='replace')
    except Exception as e:
        print(f"  [WARN] Failed to fetch {url}: {e}", file=sys.stderr)
        return None

def clean_html(text):
    text = re.sub(r'<[^>]+>', '', text or '')
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:250]

def parse_rss(xml_content, max_items=5):
    articles = []
    if not xml_content:
        return articles
    try:
        # Fix unescaped ampersands
        xml_content = re.sub(r'&(?!(amp|lt|gt|quot|apos);)', '&amp;', xml_content)
        root = ET.fromstring(xml_content)
        channel = root.find('channel')
        if channel is None:
            return articles
        for item in channel.findall('item')[:max_items]:
            title = clean_html(item.findtext('title', ''))
            link  = (item.findtext('link', '') or '').strip()
            desc  = clean_html(item.findtext('description', ''))
            src   = clean_html(item.findtext('source', ''))
            if title and link and link.startswith('http'):
                articles.append({'title': title, 'link': link, 'desc': desc, 'source': src})
    except Exception as e:
        print(f"  [WARN] Parse error: {e}", file=sys.stderr)
    return articles

def bulan_indonesia(date_str):
    bulan = {
        'January':'Januari','February':'Februari','March':'Maret',
        'April':'April','May':'Mei','June':'Juni','July':'Juli',
        'August':'Agustus','September':'September','October':'Oktober',
        'November':'November','December':'Desember'
    }
    for en, id_ in bulan.items():
        date_str = date_str.replace(en, id_)
    return date_str

def main():
    wita = timezone(timedelta(hours=8))
    now  = datetime.now(wita)
    today     = now.strftime('%Y-%m-%d')
    today_idf = bulan_indonesia(now.strftime('%-d %B %Y'))

    SOURCES = [
        {
            'name': '🏛️ Berita Resmi & Nasional',
            'url': 'https://news.google.com/rss/search?q=bali+pariwisata+pemerintah&hl=id&gl=ID&ceid=ID:id',
            'max': 5
        },
        {
            'name': '📰 Tribun Bali',
            'url': 'https://bali.tribunnews.com/rss',
            'max': 5
        },
        {
            'name': '💰 Ekonomi & Investasi Bali',
            'url': 'https://news.google.com/rss/search?q=ekonomi+investasi+bali+2026&hl=id&gl=ID&ceid=ID:id',
            'max': 4
        },
        {
            'name': '🌍 Bali International News (EN)',
            'url': 'https://news.google.com/rss/search?q=bali+tourism+travel&hl=en&gl=US&ceid=US:en',
            'max': 4
        },
    ]

    filename = f"content/artikel/ringkasan-berita-bali-{today}.md"
    if os.path.exists(filename):
        print(f"Already exists: {filename}")
        return

    lines = []
    lines.append(f"""---
title: "Ringkasan Berita Bali — {today_idf}"
date: {today}T05:00:00+08:00
description: "Kumpulan berita terkini seputar Bali dari berbagai media terpercaya pada {today_idf} — pariwisata, ekonomi, budaya, dan lingkungan."
categories: ["Berita"]
tags: ["ringkasan berita", "berita bali", "harian"]
image: "https://images.pexels.com/photos/2166559/pexels-photo-2166559.jpeg?auto=compress&cs=tinysrgb&w=1200"
image_credit: "Foto: Pexels"
---

Berikut ringkasan berita terpenting seputar Bali yang dikumpulkan dari berbagai media terpercaya pada **{today_idf}**. Klik judul untuk membaca artikel lengkap di sumber aslinya.

""")

    total = 0
    for src in SOURCES:
        print(f"Fetching: {src['name']}")
        xml  = fetch_rss(src['url'])
        arts = parse_rss(xml, src['max'])
        if not arts:
            print(f"  [SKIP] No articles")
            continue
        lines.append(f"\n## {src['name']}\n")
        for a in arts:
            lines.append(f"### [{a['title']}]({a['link']})\n")
            if a['desc']:
                lines.append(f"{a['desc']}...\n")
            src_label = f" — *{a['source']}*" if a['source'] else ''
            lines.append(f"\n🔗 **[Baca selengkapnya →]({a['link']})**{src_label}\n\n---\n")
            total += 1
        print(f"  ✅ {len(arts)} articles")

    lines.append(f"""

## ℹ️ Tentang Ringkasan Ini

Halaman ini adalah **agregasi berita** dari berbagai media terpercaya. Bali Kini tidak mengklaim kepemilikan atas konten yang ditautkan — semua kredit milik media sumber masing-masing.

- Total berita: **{total} artikel**
- Diperbarui otomatis setiap hari pukul **05:00 WITA**
- Sumber: Google News, Tribun Bali, dan media nasional

*Untuk artikel eksklusif dan analisis data Bali → [baca artikel Bali Kini](/artikel/)*
""")

    os.makedirs('content/artikel', exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"\n✅ Created: {filename} ({total} articles)")

if __name__ == '__main__':
    main()
