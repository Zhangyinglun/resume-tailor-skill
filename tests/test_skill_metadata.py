from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml


class SkillMetadataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parent.parent

    def test_skill_frontmatter_and_references(self) -> None:
        skill_path = self.repo_root / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")
        parts = re.split(r"^---\s*$", content, maxsplit=2, flags=re.MULTILINE)
        self.assertGreaterEqual(len(parts), 3)
        frontmatter = yaml.safe_load(parts[1])
        self.assertEqual(set(frontmatter), {"name", "description"})
        self.assertEqual(frontmatter["name"], "monkey-resume")
        self.assertLessEqual(len(content.splitlines()), 500)

        for relative_path in re.findall(r"`((?:references|scripts)/[^`]+)`", content):
            path_without_placeholder = relative_path.split(" ", 1)[0]
            self.assertTrue(
                (self.repo_root / path_without_placeholder).exists(),
                path_without_placeholder,
            )

    def test_package_has_no_client_specific_adapters(self) -> None:
        client_specific_paths = (
            "CLAUDE.md",
            ".claude",
            ".opencode",
            "agents/openai.yaml",
            "install/agent-install.yaml",
            "scripts/check_agent_platform_support.py",
        )
        present = [
            path
            for path in client_specific_paths
            if (self.repo_root / path).exists()
        ]
        self.assertEqual(present, [])

    def test_restricted_vendor_content_is_not_bundled(self) -> None:
        vendor_root = self.repo_root / "vendor"
        bundled_files = [
            path for path in vendor_root.rglob("*") if path.is_file()
        ] if vendor_root.exists() else []
        self.assertEqual(bundled_files, [])

    def test_skill_contains_model_projection_workflow_terms(self) -> None:
        skill_path = self.repo_root / "SKILL.md"
        skill_text = skill_path.read_text(encoding="utf-8")
        for term in (
            "projection-plan.json",
            "projection-language.json",
            "Resume Language Optimizer",
            "Content Fit Feedback",
            "projection_plan_manager.py",
        ):
            self.assertIn(term, skill_text)


if __name__ == "__main__":
    unittest.main()
