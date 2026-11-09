"""Tests for template generation, installation, and retrieval."""

import tempfile
import unittest
from pathlib import Path

from ot.templates import DEFAULT_TEMPLATES, get_template, install_default_templates, render_template


class TestTemplates(unittest.TestCase):
    def test_default_templates_collection(self):
        self.assertIn("tasks/default.md", DEFAULT_TEMPLATES)
        self.assertIn("tasks/bug.md", DEFAULT_TEMPLATES)
        self.assertIn("tasks/feature.md", DEFAULT_TEMPLATES)
        self.assertIn("tasks/epic.md", DEFAULT_TEMPLATES)
        self.assertIn("tasks/chore.md", DEFAULT_TEMPLATES)
        self.assertIn("tasks/spike.md", DEFAULT_TEMPLATES)
        self.assertIn("meetings/grooming.md", DEFAULT_TEMPLATES)
        self.assertIn("meetings/planning.md", DEFAULT_TEMPLATES)
        self.assertIn("meetings/retrospective.md", DEFAULT_TEMPLATES)
        self.assertIn("meetings/ideation.md", DEFAULT_TEMPLATES)
        self.assertIn("shared/comment.md", DEFAULT_TEMPLATES)

    def test_install_default_templates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / ".ot").mkdir()

            installed = install_default_templates(root)
            self.assertEqual(installed, len(DEFAULT_TEMPLATES))

            # Calling again without overwrite should install 0
            reinstalled = install_default_templates(root)
            self.assertEqual(reinstalled, 0)

            # Retrieve local template
            bug_tmpl = get_template("tasks/bug.md", root)
            self.assertIsNotNone(bug_tmpl)
            self.assertIn("Steps to Reproduce", bug_tmpl)

    def test_render_template_and_cli_custom_templates(self):
        import io
        import shutil
        from contextlib import redirect_stdout
        from ot.cli import main

        rendered = render_template("Hello {{name}}, status={{ status }}, missing={{unknown}}", {"name": "Alice", "status": "planned"})
        self.assertEqual(rendered, "Hello Alice, status=planned, missing={{unknown}}")

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            sample_src = Path(__file__).resolve().parent.parent / "examples" / "sample-project"
            shutil.copytree(sample_src, root, dirs_exist_ok=True)
            install_default_templates(root)

            # Customize bug.md and shared/comment.md
            custom_bug = root / ".ot" / "templates" / "tasks" / "bug.md"
            custom_bug.write_text(
                "---\nid: {{id}}\ntitle: {{title}}\ntype: bug\nstatus: {{status}}\ncreated_at: {{created_at}}\ntags:\n  - custom-bug\n---\n\n# {{title}}\n\n## Custom Bug Section\nCustom template content.\n",
                encoding="utf-8",
            )
            custom_comment = root / ".ot" / "templates" / "shared" / "comment.md"
            custom_comment.write_text(
                "### Comment by {{author_name}} on {{timestamp}}\n<!-- comment-id: {{comment_id}} -->\n\n[Custom Comment] {{body}}\n",
                encoding="utf-8",
            )

            buf = io.StringIO()
            with redirect_stdout(buf):
                ret = main(["-C", str(root), "task", "create", "Custom Template Bug", "-t", "bug", "--no-edit"])
            self.assertEqual(ret, 0)

            with redirect_stdout(io.StringIO()):
                ret_c = main(["-C", str(root), "task", "comment", "Custom Template Bug", "Verified reproduction"])
            self.assertEqual(ret_c, 0)

            bug_file = root / ".ot" / "tasks" / "CustomTemplateBug" / "index.md"
            self.assertTrue(bug_file.is_file())
            content = bug_file.read_text(encoding="utf-8")
            self.assertIn("## Custom Bug Section", content)
            self.assertIn("- custom-bug", content)
            self.assertIn("[Custom Comment] Verified reproduction", content)


if __name__ == "__main__":
    unittest.main()
