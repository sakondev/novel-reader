"""Reader smoke tests; standard library only."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "reader"))
from build import build, inline_md, layout, render_markdown, slugify

class ReaderTests(unittest.TestCase):
    def test_escape_html(self):
        self.assertIn("&lt;script&gt;", render_markdown("<script>alert(1)</script>"))
        self.assertNotIn("<script>", render_markdown("<script>alert(1)</script>"))

    def test_markdown_and_scene_separator(self):
        data = "# หัวเรื่อง\n\nข้อความ *เน้น*\n\n* * *\n\nต่อไป"
        output = render_markdown(data)
        self.assertIn("<h1>หัวเรื่อง</h1>", output)
        self.assertIn("<em>เน้น</em>", output)
        self.assertIn("<hr ", output)
        self.assertEqual(output.count("<p>"), 2)

    def test_pages_request_no_indexing(self):
        page = layout("Test", "<main>Text</main>", None, True, "../")
        self.assertIn('name="robots" content="noindex, nofollow', page)
        self.assertIn('name="googlebot" content="noindex, nofollow', page)
        self.assertIn('name="bingbot" content="noindex, nofollow', page)

    def test_clean_chapter_urls_and_resume_prompt(self):
        with tempfile.TemporaryDirectory() as temp:
            from pathlib import Path
            build(Path(temp))
            book = Path(temp) / "pick-up-grimoire-become-a-mage"
            clean = (book / "chapter-0001" / "index.html").read_text(encoding="utf-8")
            legacy = (book / "chapter-0001.html").read_text(encoding="utf-8")
            toc = (book / "index.html").read_text(encoding="utf-8")
            self.assertIn('id="resumePrompt"', clean)
            self.assertNotIn('id="audioToggle"', clean)
            self.assertNotIn('id="ttsPanel"', clean)
            self.assertIn('class="bottom-nav"', clean)
            self.assertIn("I Picked Up a Grimoire and Became a Wizard", clean)
            self.assertIn("I Picked Up a Grimoire and Became a Wizard", toc)
            library = (Path(temp) / "index.html").read_text(encoding="utf-8")
            self.assertIn("I Picked Up a Grimoire and Became a Wizard", library)
            self.assertIn("เก็บคัมภีร์เวทมนตร์ได้ เลยกลายเป็นจอมเวทซะงั้น", library)
            self.assertIn('id="openChapterPicker"', clean)
            self.assertIn('id="chapterSearch"', clean)
            self.assertIn('class="bottom-nav"', clean)
            self.assertIn('href="../chapter-0002/"', clean)
            self.assertIn("family=Google+Sans", clean)
            self.assertIn("family=Noto+Sans+Thai", clean)
            self.assertIn('id="resumeReading"', clean)
            self.assertIn('href="../../assets/style.css"', clean)
            self.assertIn('href="chapter-0001/"', toc)
            self.assertIn("ตอนที่ 1 - มาฝึกเป็นจอมเวทกันเถอะ (1)", toc)
            self.assertIn("เลือกตอน / ค้นหาตอน", clean)
            self.assertNotIn("⌄", clean) 
            self.assertIn('url=chapter-0001/', legacy)
            self.assertIn('noindex', legacy)

    def test_audio_manifest_player_and_no_tts(self):
        import json
        from unittest.mock import patch
        import build as builder
        with tempfile.TemporaryDirectory() as source, tempfile.TemporaryDirectory() as output:
            root = Path(source)
            book = root / "Example Book"
            translated = book / "translated"
            translated.mkdir(parents=True)
            (translated / "chapter-0001.md").write_text("# บทที่ 1\\n\\nข้อความ", encoding="utf-8")
            (translated / "chapter-0002.md").write_text("# บทที่ 2\\n\\nข้อความ", encoding="utf-8")
            (book / "audio.json").write_text(json.dumps({"chapters": {"1": {"url": "https://audio.example.com/chapter-1.mp3"}}}), encoding="utf-8")
            with patch.object(builder, "ROOT", root):
                (root / "reader").mkdir()
                from shutil import copyfile
                original_reader = Path(__file__).resolve().parents[1] / "reader"
                for name in ("style.css", "reader.js", "robots.txt"):
                    copyfile(original_reader / name, root / "reader" / name)
                builder.build(Path(output))
            slug = Path(output) / "example-book"
            first = (slug / "chapter-0001" / "index.html").read_text(encoding="utf-8")
            second = (slug / "chapter-0002" / "index.html").read_text(encoding="utf-8")
            self.assertIn('id="audioToggle"', first)
            self.assertIn('id="chapterAudio"', first)
            self.assertIn("https://audio.example.com/chapter-1.mp3", first)
            self.assertNotIn('id="audioToggle"', second)
            self.assertNotIn("ttsPanel", first)
            script = (Path(output) / "assets" / "reader.js").read_text(encoding="utf-8")
            self.assertNotIn("speechSynthesis", script)

    def test_slug(self):
        self.assertEqual(slugify("Pick Up Grimoire - Become a Mage"), "pick-up-grimoire-become-a-mage")

if __name__ == "__main__":
    unittest.main()
