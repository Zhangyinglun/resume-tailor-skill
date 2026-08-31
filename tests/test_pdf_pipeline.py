from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

try:
    import pdfplumber
    import reportlab
except ImportError:  # pragma: no cover - dependency check reports this separately.
    pdfplumber = None
    reportlab = None

from scripts.check_pdf_quality import build_quality_report
from scripts.evidence_ledger_manager import (
    initialize_workspace,
    rebuild_tailoring_manifest,
)


def sample_resume(*, invalid: bool = False) -> dict[str, Any]:
    bullets = [
        "Built distributed APIs using Python and AWS, reducing latency by 20%.",
        "Automated deployment validation with Python, preventing invalid releases.",
        "Designed recovery workflows across AWS services, improving resilience.",
        "Implemented request tracing with Python, enabling faster incident diagnosis.",
    ]
    return {
        "name": "[Company]" if invalid else "Alex Chen",
        "contact": (
            "missing"
            if invalid
            else "Seattle | +1 206-555-0100 | alex@example.com | linkedin.com/in/alex"
        ),
        "summary": "Backend engineer building distributed systems and cloud services.",
        "skills": [{"category": "Languages", "items": "Python, Go, C++"}],
        "experience": [
            {
                "company": "Example Corp",
                "title": "Software Engineer",
                "location": "Seattle",
                "dates": "2020 - Present",
                "bullets": bullets,
            }
        ],
        "education": [
            {
                "school": "Example University",
                "degree": "B.S. Computer Science",
                "dates": "2016 - 2020",
            }
        ],
    }


def prepare_audited_workspace(root: Path, resume: dict[str, Any]) -> Path:
    initialize_workspace(root, resume)
    rebuild_tailoring_manifest(root)
    return root / "cache" / "resume-working.json"


class PdfQualityPolicyTests(unittest.TestCase):
    def test_excess_whitespace_is_warning_not_failure(self) -> None:
        report = build_quality_report(
            page_count=1,
            width_mm=210.0,
            height_mm=297.0,
            has_text=True,
            html_leak_count=0,
            placeholders=[],
            margins={"top": 25.0, "bottom": 40.0, "left": 30.0, "right": 30.0},
            missing_sections=[],
            contact={"email": True, "phone": True, "linkedin": False},
            missing_keywords=[],
            provided_keywords=[],
            layout_warnings=[],
            margin_thresholds={
                "min_bottom_mm": 3.0,
                "max_bottom_mm": 8.0,
                "min_top_mm": 3.0,
                "max_top_mm": 20.0,
                "min_side_mm": 10.0,
                "max_side_mm": 25.0,
            },
        )
        self.assertEqual(report["verdict"], "PASS")
        warning_check = next(
            check for check in report["checks"] if check["name"] == "layout_warnings"
        )
        self.assertTrue(warning_check["detail"]["warnings"])


@unittest.skipIf(reportlab is None or pdfplumber is None, "PDF dependencies unavailable")
class PdfPipelineTests(unittest.TestCase):
    def test_renderer_rejects_skill_package_output(self) -> None:
        from templates.modern_resume_template import generate_resume

        repo_root = Path(__file__).resolve().parent.parent
        with self.assertRaisesRegex(ValueError, "outside the Skill package"):
            generate_resume(
                "resume.pdf",
                sample_resume(),
                base_dir=str(repo_root / "resume_output"),
            )

    def test_renderer_escapes_user_markup(self) -> None:
        from scripts.check_pdf_quality import check_pdf_file
        from templates.modern_resume_template import generate_resume

        assert pdfplumber is not None
        resume = sample_resume()
        resume["summary"] = "Built R&D services with Java Map<K,V> and C++ & C#."
        with tempfile.TemporaryDirectory() as temp_dir:
            with contextlib.redirect_stdout(io.StringIO()):
                output = Path(generate_resume("resume.pdf", resume, base_dir=temp_dir))
            self.assertTrue(output.exists())
            with pdfplumber.open(output) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            self.assertIn("Map<K,V>", text)
            self.assertIn("R&D", text)
            report = check_pdf_file(output)
            html_check = next(check for check in report["checks"] if check["name"] == "html_leak")
            self.assertTrue(html_check["passed"])
            geometry_check = next(
                check for check in report["checks"] if check["name"] == "text_geometry"
            )
            self.assertIn("sparse_trailing_line_count", geometry_check["detail"])

    def test_generator_blocks_when_mandatory_audit_inputs_are_missing(self) -> None:
        import scripts.generate_final_resume as cli

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "resume.json"
            source.write_text(json.dumps(sample_resume()), encoding="utf-8")
            output_dir = root / "output"
            argv = [
                "generate_final_resume.py",
                "--input-json",
                str(source),
                "--output-file",
                "resume.pdf",
                "--output-dir",
                str(output_dir),
            ]
            stderr = io.StringIO()
            with mock.patch.object(sys, "argv", argv), contextlib.redirect_stderr(stderr):
                result = cli.main()

            self.assertEqual(result, 1)
            self.assertIn("factual audit", stderr.getvalue().lower())
            self.assertFalse((output_dir / "resume.pdf").exists())

    def test_generator_rejects_output_dir_inside_skill_package(self) -> None:
        import scripts.generate_final_resume as cli

        repo_root = Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory() as temp_dir:
            source = prepare_audited_workspace(Path(temp_dir), sample_resume())
            argv = [
                "generate_final_resume.py",
                "--input-json",
                str(source),
                "--output-file",
                "resume.pdf",
                "--output-dir",
                str(repo_root / "resume_output"),
            ]
            stderr = io.StringIO()
            with mock.patch.object(sys, "argv", argv), contextlib.redirect_stderr(stderr):
                result = cli.main()

            self.assertEqual(result, 1)
            self.assertIn("outside the Skill package", stderr.getvalue())

    def test_failed_candidate_preserves_existing_pdfs(self) -> None:
        import scripts.generate_final_resume as cli

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output_dir = root / "output"
            output_dir.mkdir()
            current = output_dir / "resume.pdf"
            other = output_dir / "previous-good.pdf"
            current.write_bytes(b"accepted-current")
            other.write_bytes(b"accepted-other")
            source = prepare_audited_workspace(root, sample_resume(invalid=True))

            argv = [
                "generate_final_resume.py",
                "--input-json",
                str(source),
                "--output-file",
                "resume.pdf",
                "--output-dir",
                str(output_dir),
            ]
            with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()):
                result = cli.main()

            self.assertEqual(result, 2)
            self.assertEqual(current.read_bytes(), b"accepted-current")
            self.assertEqual(other.read_bytes(), b"accepted-other")
            self.assertTrue(list((output_dir / "rejected").glob("*.pdf")))

    def test_passing_candidate_archives_then_publishes(self) -> None:
        import scripts.generate_final_resume as cli

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output_dir = root / "output"
            output_dir.mkdir()
            current = output_dir / "resume.pdf"
            current.write_bytes(b"accepted-current")
            source = prepare_audited_workspace(root, sample_resume())

            argv = [
                "generate_final_resume.py",
                "--input-json",
                str(source),
                "--output-file",
                "resume.pdf",
                "--output-dir",
                str(output_dir),
                "--auto-fit",
            ]
            with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()):
                result = cli.main()

            self.assertEqual(result, 0)
            self.assertTrue(current.read_bytes().startswith(b"%PDF"))
            self.assertTrue(list((output_dir / "backup").rglob("resume_old_*.pdf")))

    def test_generator_accepts_valid_warning_disposition(self) -> None:
        import scripts.generate_final_resume as cli

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output_dir = root / "output"
            # 2 bullets in 1 experience entry triggers bullet_density advisory warning
            sparse_resume = sample_resume()
            sparse_resume["experience"][0]["bullets"] = [
                "Built reliable APIs using Python, improving system uptime.",
                "Automated release testing with Python, preventing failed rollouts.",
            ]
            source = prepare_audited_workspace(root, sparse_resume)

            # Add valid disposition
            manifest_path = root / "cache" / "resume-changes.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["warning_dispositions"] = [
                {
                    "finding": "bullet_density",
                    "status": "accepted",
                    "reason": "Compact resume format accepted for this target position.",
                }
            ]
            manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

            argv = [
                "generate_final_resume.py",
                "--input-json",
                str(source),
                "--output-file",
                "resume.pdf",
                "--output-dir",
                str(output_dir),
                "--auto-fit",
            ]
            with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()):
                result = cli.main()

            self.assertEqual(result, 0)
            self.assertTrue((output_dir / "resume.pdf").exists())

    def test_generator_blocks_disposition_with_empty_reason_or_wrong_finding(self) -> None:
        import scripts.generate_final_resume as cli

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output_dir = root / "output"
            sparse_resume = sample_resume()
            sparse_resume["experience"][0]["bullets"] = [
                "Built reliable APIs using Python, improving system uptime.",
                "Automated release testing with Python, preventing failed rollouts.",
            ]
            source = prepare_audited_workspace(root, sparse_resume)
            manifest_path = root / "cache" / "resume-changes.json"

            # 1. Empty reason should block
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["warning_dispositions"] = [
                {"finding": "bullet_density", "status": "accepted", "reason": "   "}
            ]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            argv = [
                "generate_final_resume.py",
                "--input-json",
                str(source),
                "--output-file",
                "resume.pdf",
                "--output-dir",
                str(output_dir),
            ]
            with mock.patch.object(sys, "argv", argv), contextlib.redirect_stderr(io.StringIO()):
                result = cli.main()
            self.assertEqual(result, 2)

            # 2. Mismatched finding name should block
            manifest["warning_dispositions"] = [
                {"finding": "unrelated_check", "status": "accepted", "reason": "Valid reason"}
            ]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with mock.patch.object(sys, "argv", argv), contextlib.redirect_stderr(io.StringIO()):
                result = cli.main()
            self.assertEqual(result, 2)


if __name__ == "__main__":
    unittest.main()
