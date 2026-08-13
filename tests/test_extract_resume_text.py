from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.extract_resume_text import extract_resume_text


class ExtractResumeTextTests(unittest.TestCase):
    def test_extracts_utf8_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "resume.txt"
            path.write_text("Résumé\nExperience", encoding="utf-8")
            self.assertEqual(extract_resume_text(path), "Résumé\nExperience")

    def test_extracts_docx_paragraphs(self) -> None:
        document_xml = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body><w:p><w:r><w:t>Alex Chen</w:t></w:r></w:p>
  <w:p><w:r><w:t>Experience</w:t></w:r></w:p></w:body>
</w:document>"""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "resume.docx"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("word/document.xml", document_xml)
            self.assertEqual(extract_resume_text(path), "Alex Chen\nExperience")

    def test_rejects_unsupported_format(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "resume.rtf"
            path.write_text("resume", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Unsupported"):
                extract_resume_text(path)


if __name__ == "__main__":
    unittest.main()
