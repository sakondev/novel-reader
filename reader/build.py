#!/usr/bin/env python3
"""Small, dependency-free Markdown novel reader static site generator."""
import argparse
import html
import re
import shutil
import unicodedata
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
CHAPTER_RE = re.compile(r"chapter-(\d+)\.md$", re.I)

def slugify(value):
    value = unicodedata.normalize("NFKC", value).lower()
    value = re.sub(r"[^\w\- ]+", "", value, flags=re.UNICODE).strip()
    return re.sub(r"[-\s_]+", "-", value) or "novel"

def inline_md(text):
    text = html.escape(text.strip())
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return text

def render_markdown(raw):
    result = []
    blocks = re.split(r"\n\s*\n", raw.replace("\r\n", "\n").strip())
    for block in blocks:
        block = block.strip()
        if not block: continue
        if block.startswith("> Final") or block.startswith("> Reviewed candidate"):
            continue
        if block.startswith("> ต้นฉบับ:"): continue
        if re.fullmatch(r"(\*\s*){3}", block):
            result.append("<hr aria-label='แบ่งฉาก'>")
        elif block.startswith("# "):
            result.append("<h1>" + inline_md(block[2:]) + "</h1>")
        elif block.startswith("## "):
            result.append("<h2>" + inline_md(block[3:]) + "</h2>")
        elif block.startswith("> "):
            result.append("<blockquote>" + inline_md(block[2:]) + "</blockquote>")
        else:
            result.append("<p>" + "<br>".join(inline_md(s) for s in block.split("\n")) + "</p>")
    return "\n".join(result)

def title_for(content, fallback):
    for line in content.splitlines():
        if line.startswith("# "): return line[2:].strip()
    return fallback

def book_title(path):
    config = path / "novel.yaml"
    if config.exists():
        data = config.read_text(encoding="utf-8")
        for k in ("title_th", "title_en"):
            m = re.search(rf"(?m)^{k}:\s*[\"']?([^\r\n\"']+)", data)
            if m and m.group(1).strip(): return m.group(1).strip()
    return path.name

def layout(title, body, css, js, base, chapter=False):
    script = f'<script defer src="{base}assets/reader.js"></script>' if js else ""
    return f"""<!doctype html><html lang="th"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#f7f3eb"><meta name="description" content="{html.escape(title, quote=True)}">
<title>{html.escape(title)} · Novel Reader</title><link rel="stylesheet" href="{base}assets/style.css"></head>
<body><a class="skip" href="#content">ข้ามไปเนื้อหา</a><header class="site-head"><a class="brand" href="{base}index.html">NOVEL READER</a>
<div class="tools"><button id="fontDown" type="button" aria-label="ลดขนาดตัวอักษร">A−</button><button id="fontUp" type="button" aria-label="เพิ่มขนาดตัวอักษร">A+</button>
<button id="theme" type="button" aria-label="เปลี่ยนธีม">◐</button></div></header>
{body}<footer>Novel Reader · บันทึกตำแหน่งการอ่านบนอุปกรณ์ของคุณ</footer>{script}</body></html>"""

def build(destination):
    destination = destination.resolve()
    if destination == ROOT or ROOT in destination.parents and destination.name != "_site":
        raise ValueError("Output must be a separate site directory, not overwrite source files")
    destination.mkdir(parents=True, exist_ok=True)
    assets = destination / "assets"
    assets.mkdir(exist_ok=True)
    for f in ("style.css", "reader.js"): shutil.copyfile(ROOT / "reader" / f, assets / f)
    books = []
    for directory in sorted(ROOT.iterdir()):
        if not directory.is_dir() or directory.name.startswith("."): continue
        chapters = []
        for md in sorted((directory / "translated").glob("chapter-*.md")):
            m = CHAPTER_RE.fullmatch(md.name)
            if m: chapters.append((int(m.group(1)), md))
        if not chapters: continue
        slug = slugify(directory.name)
        if any(x[0] == slug for x in books): raise ValueError(f"Book slug collision: {slug}")
        title = book_title(directory)
        dest = destination / slug
        dest.mkdir(exist_ok=True)
        for index, (num, md) in enumerate(chapters):
            raw = md.read_text(encoding="utf-8-sig")
            chapter_title = title_for(raw, f"บทที่ {num}")
            prev_link = f'<a href="chapter-{chapters[index - 1][0]:04}.html">← ตอนก่อนหน้า</a>' if index else "<span></span>"
            next_link = f'<a href="chapter-{chapters[index + 1][0]:04}.html">ตอนถัดไป →</a>' if index < len(chapters)-1 else "<span></span>"
            nav = f'<nav class="chapter-nav" aria-label="นำทางตอน">{prev_link}<a href="index.html">สารบัญ</a>{next_link}</nav>'
            body = f'<main id="content" class="reader"><div class="eyebrow"><a href="index.html">{html.escape(title)}</a></div><article>{render_markdown(raw)}</article>{nav}</main>'
            (dest / f"chapter-{num:04}.html").write_text(layout(chapter_title, body, None, True, "../"), encoding="utf-8")
        cards = "\n".join(f'<li><a href="chapter-{num:04}.html"><span>ตอนที่ {num}</span><span aria-hidden="true">→</span></a></li>' for num, _ in chapters)
        page = f'<main id="content" class="index"><p class="eyebrow"><a href="../index.html">← นิยายทั้งหมด</a></p><h1>{html.escape(title)}</h1><p class="sub">จำนวน {len(chapters)} ตอน</p><ol class="chapters">{cards}</ol></main>'
        (dest / "index.html").write_text(layout(title, page, None, True, "../"), encoding="utf-8")
        books.append((slug,title,len(chapters),chapters[0][0]))
    if not books: raise ValueError("No canonical translated/chapter-NNNN.md files found")
    items = "\n".join(f'<a class="book-card" href="{quote(slug)}/index.html"><span class="book-title">{html.escape(title)}</span><span>{count} ตอน <span aria-hidden="true">→</span></span></a>' for slug,title,count,_ in books)
    home = '<main id="content" class="index"><p class="eyebrow">ห้องสมุดของคุณ</p><h1>อ่านนิยาย</h1><p class="sub">เลือกเรื่องที่ต้องการอ่าน</p><div class="books">' + items + '</div></main>'
    (destination / "index.html").write_text(layout("ห้องสมุด",home,None,True,""), encoding="utf-8")
    (destination / ".nojekyll").touch()
    print(f"Built {len(books)} books / {sum(v[2] for v in books)} chapters at {destination}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,default=ROOT/"_site")
    args = parser.parse_args()
    build(args.out)
