import unittest
from backend.render_pipeline.content_shaper import PromptContentShaper
from backend.core import entities as e


class TestPromptContentShaper(unittest.TestCase):

    def setUp(self):
        self.shaper = PromptContentShaper()

    def test_non_template_file_passes_through_unchanged(self):
        content = "hello §fsul§ world"
        file = e.File(name="README.md", truncation_spec=None)
        result = self.shaper.process(content, file)
        self.assertEqual(result, "hello §fsul§ world")

    def test_template_file_placeholder_substitution(self):
        content = "§fsul§ path §fsur§\n§fel§ path §fer§"
        file = e.File(name="prompt.output-template", truncation_spec=None)
        result = self.shaper.process(content, file)
        self.assertEqual(result, "< path >\n</ path >")

    def test_template_file_no_placeholder_tokens_remain(self):
        content = "§po§ heading §pc§\n§fsul§ a §fsur§\n§llul§ b §llur§\n§mm§ tag §mm§"
        file = e.File(name="x.output-template", truncation_spec=None)
        result = self.shaper.process(content, file)
        self.assertNotIn("§", result)

    def test_truncation_applies_after_substitution(self):
        content = "line1\n§fsul§ content §fsur§\nline3\nline4"
        spec = e.TruncationSpec(tail_lines=2, from_line=None, up_to=None)
        file = e.File(name="test.output-template", truncation_spec=spec)
        result = self.shaper.process(content, file)
        self.assertEqual(result, "**truncated**\nline3\nline4")

    def test_none_file_passes_through_no_substitution(self):
        content = "plain text §fsul§"
        result = self.shaper.process(content, None)
        self.assertEqual(result, "plain text §fsul§")

    def test_from_line_on_template(self):
        content = "§fsul§ start §fsur§\nmiddle\n§llul§ end §llur§"
        spec = e.TruncationSpec(tail_lines=None, from_line=r"^middle", up_to=None)
        file = e.File(name="t.output-template", truncation_spec=spec)
        result = self.shaper.process(content, file)
        self.assertEqual(result, "middle\n< end >")

    def test_up_to_on_template(self):
        content = "§fsul§ start §fsur§\nmiddle\n§llul§ end §llur§"
        spec = e.TruncationSpec(tail_lines=None, from_line=None, up_to=r"^middle")
        file = e.File(name="t.output-template", truncation_spec=spec)
        result = self.shaper.process(content, file)
        self.assertEqual(result, "< start >")