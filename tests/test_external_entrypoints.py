from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class ExternalEntrypointTests(unittest.TestCase):
    def test_help_commands_work_outside_repository(self) -> None:
        repo_root = Path(__file__).resolve().parent.parent
        scripts = (
            "resume_cache_manager.py",
            "check_content_quality.py",
            "generate_quality_report.py",
            "extract_resume_text.py",
            "generate_final_resume.py",
            "check_pdf_quality.py",
            "check_pdf_geometry.py",
            "evidence_ledger_manager.py",
            "audit_factual_integrity.py",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            for script in scripts:
                with self.subTest(script=script):
                    result = subprocess.run(
                        [sys.executable, str(repo_root / "scripts" / script), "--help"],
                        cwd=temp_dir,
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        check=False,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)

    def test_cache_manager_rejects_skill_directory_as_workspace(self) -> None:
        repo_root = Path(__file__).resolve().parent.parent
        result = subprocess.run(
            [
                sys.executable,
                str(repo_root / "scripts" / "resume_cache_manager.py"),
                "reset",
                "--workspace",
                str(repo_root),
            ],
            cwd=repo_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("outside the Skill package", result.stderr)


if __name__ == "__main__":
    unittest.main()
