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

def book_title_en(path):
    config = path / "novel.yaml"
    if config.exists():
        m = re.search(r'(?m)^title_en:\s*["\']?([^\r\n"\']+)', config.read_text(encoding="utf-8"))
        if m and m.group(1).strip(): return m.group(1).strip()
    return ""

def layout(title, body, css, js, base, chapter=False):
    script = f'<script defer src="{base}assets/reader.js"></script>' if js else ""
    font_css = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;600;700&family=Noto+Sans+Thai:wght@400;500;600;700&display=swap" rel="stylesheet">'
    body_class = ' class="chapter-view"' if chapter else ""
    listen_button = '<button id="ttsToggle" type="button" aria-controls="ttsPanel" aria-expanded="false" aria-label="เปิดตัวอ่านออกเสียง">🔊 ฟัง</button>' if chapter else ""
    return f"""<!doctype html><html lang="th"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow, noarchive, nosnippet, noimageindex"><meta name="googlebot" content="noindex, nofollow, noarchive, nosnippet, noimageindex"><meta name="bingbot" content="noindex, nofollow, noarchive, nosnippet, noimageindex">
<meta name="theme-color" content="#f7f3eb"><meta name="description" content="{html.escape(title, quote=True)}">
<title>{html.escape(title)} · Novel Reader</title>{font_css}<link rel="stylesheet" href="{base}assets/style.css"></head>
<body{body_class}><a class="skip" href="#content">ข้ามไปเนื้อหา</a><header class="site-head"><a class="brand" href="{base}index.html">NOVEL READER</a>
<div class="tools">{listen_button}<button id="fontDown" type="button" aria-label="ลดขนาดตัวอักษร">A−</button><span id="fontSizeValue" class="font-value" aria-live="polite">19px</span><button id="fontUp" type="button" aria-label="เพิ่มขนาดตัวอักษร">A+</button>
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
        english_title = book_title_en(directory)
        subtitle = f'<p class="book-subtitle" lang="en">{html.escape(english_title)}</p>' if english_title and english_title != title else ""
        dest = destination / slug
        dest.mkdir(exist_ok=True)
        for index, (num, md) in enumerate(chapters):
            raw = md.read_text(encoding="utf-8-sig")
            chapter_title = title_for(raw, f"บทที่ {num}")
            prev_link = f'<a href="../chapter-{chapters[index - 1][0]:04}/">← ตอนก่อนหน้า</a>' if index else "<span></span>"
            next_link = f'<a href="../chapter-{chapters[index + 1][0]:04}/">ตอนถัดไป →</a>' if index < len(chapters)-1 else "<span></span>"
            nav = f'<nav class="chapter-nav" aria-label="นำทางตอน">{prev_link}<a href="../index.html">สารบัญ</a>{next_link}</nav>'
            resume = '<aside class="resume-prompt" id="resumePrompt" role="region" aria-label="ตำแหน่งอ่านเดิม" hidden><span>อ่านต่อจากจุดเดิมไหม</span><div class="resume-actions"><button type="button" id="resumeReading">อ่านต่อจากจุดเดิม</button><button type="button" id="startReading">เริ่มจากด้านบน</button></div></aside>'
            picker_items = "".join(
                f'<a class="picker-chapter{" current" if chapter_num == num else ""}" href="../chapter-{chapter_num:04}/"'
                f'{" aria-current=page" if chapter_num == num else ""}>'
                f'<span>ตอนที่ {chapter_num}</span><small>{html.escape(title_for(chapter_md.read_text(encoding="utf-8-sig"), f"บทที่ {chapter_num}"))}</small></a>'
                for chapter_num, chapter_md in chapters
            )
            prev_bottom = (f'<a class="bottom-link" href="../chapter-{chapters[index - 1][0]:04}/" aria-label="ตอนก่อนหน้า">'
                           '<span class="nav-icon" aria-hidden="true">‹</span><span>ก่อนหน้า</span></a>') if index else (
                           '<span class="bottom-link unavailable" aria-disabled="true"><span class="nav-icon">‹</span><span>ก่อนหน้า</span></span>')
            next_bottom = (f'<a class="bottom-link" href="../chapter-{chapters[index + 1][0]:04}/" aria-label="ตอนถัดไป">'
                           '<span class="nav-icon" aria-hidden="true">›</span><span>ถัดไป</span></a>') if index < len(chapters)-1 else (
                           '<span class="bottom-link unavailable" aria-disabled="true"><span class="nav-icon">›</span><span>ถัดไป</span></span>')
            bottom = (f'<nav class="bottom-nav" aria-label="เลือกตอน">{prev_bottom}'
                      f'<button type="button" id="openChapterPicker" class="bottom-current" aria-haspopup="dialog" aria-controls="chapterPicker">'
                      f'<span class="bottom-current-title">ตอนที่ {num}</span><span class="bottom-current-caption">เลือกตอน / ค้นหาตอน</span></button>'
                      f'{next_bottom}</nav>')
            picker = (f'<dialog id="chapterPicker" class="chapter-picker" aria-labelledby="pickerTitle">'
                      f'<div class="picker-heading"><div><strong id="pickerTitle">เลือกตอนที่ต้องการอ่าน</strong>'
                      f'<p>ทั้งหมด {len(chapters)} ตอน</p></div><form method="dialog">'
                      f'<button type="submit" aria-label="ปิดรายการตอน">✕</button></form></div>'
                      f'<label class="picker-search-label" for="chapterSearch">ค้นหาหมายเลขหรือชื่อตอน</label>'
                      f'<input id="chapterSearch" type="search" autocomplete="off" placeholder="เช่น 12 หรือชื่อตอน..." />'
                      f'<div class="picker-results" id="chapterResults">{picker_items}</div>'
                      f'<p class="picker-empty" id="chapterEmpty" hidden>ไม่พบตอนที่ค้นหา</p></dialog>')
            tts = ('<section id="ttsPanel" class="tts-panel" aria-label="เครื่องอ่านนิยาย" hidden>'
                   '<div class="tts-heading"><strong>ฟังนิยาย</strong><span id="ttsStatus" role="status">พร้อมอ่าน</span>'
                   '<button type="button" id="ttsClose" aria-label="ปิดเครื่องอ่าน">✕</button></div>'
                   '<div class="tts-controls"><button type="button" id="ttsPlay">▶ อ่าน</button>'
                   '<button type="button" id="ttsPause" disabled>⏸ พัก</button>'
                   '<button type="button" id="ttsStop" disabled>■ หยุด</button></div>'
                   '<div class="tts-options"><label for="ttsVoice">เสียงอ่าน</label><select id="ttsVoice" aria-label="เลือกเสียงอ่าน">'
                   '<option value="">เสียงเริ่มต้น</option></select>'
                   '<label for="ttsRate">ความเร็ว</label><select id="ttsRate" aria-label="ความเร็วการอ่าน">'
                   '<option value="0.75">0.75×</option><option value="1" selected>1×</option>'
                   '<option value="1.25">1.25×</option><option value="1.5">1.5×</option></select></div>'
                   '<p class="tts-note" id="ttsNote">เลือกเสียงภาษาไทยจากอุปกรณ์ของคุณ หากมี</p></section>')
            body = f'{resume}<main id="content" class="reader"><div class="eyebrow"><a href="../index.html">{html.escape(title)}</a></div>{subtitle}<article>{render_markdown(raw)}</article>{nav}</main>{tts}{bottom}{picker}'
            chapter_dir = dest / f"chapter-{num:04}"
            chapter_dir.mkdir(exist_ok=True)
            (chapter_dir / "index.html").write_text(layout(chapter_title, body, None, True, "../../", chapter=True), encoding="utf-8")
            # Preserve bookmarked .html links without serving duplicate full-text pages.
            link = f"chapter-{num:04}/"
            redirect = ('<!doctype html><html lang="th"><head><meta charset="utf-8">'
                        '<meta name="robots" content="noindex, nofollow">'
                        f'<meta http-equiv="refresh" content="0; url={link}">'
                        f'<link rel="canonical" href="{link}">'
                        f'<title>{html.escape(chapter_title)}</title></head><body><a href="{link}">ไปยังตอนนี้</a></body></html>')
            (dest / f"chapter-{num:04}.html").write_text(redirect, encoding="utf-8")
        cards = []
        for num, md in chapters:
            heading = title_for(md.read_text(encoding="utf-8-sig"), f"บทที่ {num}")
            chapter_name = re.sub(rf"^บทที่\s*{num}\s*[-–—:]\s*", "", heading).strip()
            label = f"ตอนที่ {num} - {chapter_name}" if chapter_name != f"บทที่ {num}" else f"ตอนที่ {num}"
            cards.append(f'<li><a href="chapter-{num:04}/"><span>{html.escape(label)}</span><span aria-hidden="true">→</span></a></li>')
        cards = "\n".join(cards)
        page = f'<main id="content" class="index"><p class="eyebrow"><a href="../index.html">← นิยายทั้งหมด</a></p><h1>{html.escape(title)}</h1>{subtitle}<p class="sub">จำนวน {len(chapters)} ตอน</p><ol class="chapters">{cards}</ol></main>'
        (dest / "index.html").write_text(layout(title, page, None, True, "../"), encoding="utf-8")
        books.append((slug,title,english_title,len(chapters),chapters[0][0]))
    if not books: raise ValueError("No canonical translated/chapter-NNNN.md files found")
    items = "\n".join(f'<a class="book-card" href="{quote(slug)}/index.html"><span class="book-label"><strong class="book-title">{html.escape(title)}</strong><span class="book-subtitle" lang="en">{html.escape(english_title)}</span></span><span>{count} ตอน <span aria-hidden="true">→</span></span></a>' for slug,title,english_title,count,_ in books)
    home = '<main id="content" class="index"><p class="eyebrow">ห้องสมุดของคุณ</p><h1>อ่านนิยาย</h1><p class="sub">เลือกเรื่องที่ต้องการอ่าน</p><div class="books">' + items + '</div></main>'
    (destination / "index.html").write_text(layout("ห้องสมุด",home,None,True,""), encoding="utf-8")
    shutil.copyfile(ROOT / "reader" / "robots.txt", destination / "robots.txt")
    (destination / ".nojekyll").touch()
    print(f"Built {len(books)} books / {sum(v[3] for v in books)} chapters at {destination}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,default=ROOT/"_site")
    args = parser.parse_args()
    build(args.out)
