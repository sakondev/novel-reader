"""Reader smoke tests; standard library only."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "reader"))
from build import inline_md, render_markdown, slugify

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

    def test_slug(self):
        self.assertEqual(slugify("Pick Up Grimoire - Become a Mage"), "pick-up-grimoire-become-a-mage")

if __name__ == "__main__":
    unittest.main()
