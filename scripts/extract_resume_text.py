#!/usr/bin/env python3
"""Extract resume text from TXT, Markdown, PDF, or DOCX input."""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree


def extract_pdf_text(path: Path) -> str:
    """Extract text from a text-based PDF."""
    try:
        import pdfplumber
    except ImportError:
        raise RuntimeError(
            "PDF extraction requires pdfplumber; install requirements.txt first."
        ) from None

    with pdfplumber.open(path) as pdf:
        pages = [(page.extract_text() or "").strip() for page in pdf.pages]
    text = "\n\n".join(page for page in pages if page)
    if not text:
        raise ValueError(
            "No extractable text found in PDF. OCR the source before continuing."
        )
    return text


def extract_docx_text(path: Path) -> str:
    """Extract paragraph text from a DOCX file using the standard library."""
    try:
        with zipfile.ZipFile(path) as archive:
            document_xml = archive.read("word/document.xml")
    except (zipfile.BadZipFile, KeyError) as exc:
        raise ValueError(f"Invalid DOCX file: {path}") from exc

    root = ElementTree.fromstring(document_xml)
    namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    lines: list[str] = []
    for paragraph in root.iter(f"{namespace}p"):
        text = "".join(
            node.text or "" for node in paragraph.iter(f"{namespace}t")
        ).strip()
        if text:
            lines.append(text)
    if not lines:
        raise ValueError(f"No text found in DOCX file: {path}")
    return "\n".join(lines)


def extract_resume_text(path: Path) -> str:
    """Extract normalized text from a supported resume source."""
    suffix = path.suffix.casefold()
    if suffix in {".txt", ".md", ".markdown"}:
        return path.read_text(encoding="utf-8")
    if suffix == ".pdf":
        return extract_pdf_text(path)
    if suffix == ".docx":
        return extract_docx_text(path)
    raise ValueError(
        f"Unsupported resume format '{path.suffix}'. Use .txt, .md, .pdf, or .docx."
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract text from a resume source file")
    parser.add_argument("input_file", help="Path to .txt, .md, .pdf, or .docx input")
    parser.add_argument("--output", help="Optional UTF-8 text output path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input_file).expanduser().resolve()
    if not input_path.exists():
        print(f"Error: Input file does not exist: {input_path}", file=sys.stderr)
        return 1

    try:
        text = extract_resume_text(input_path)
        if args.output:
            output_path = Path(args.output).expanduser().resolve()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(text.rstrip() + "\n", encoding="utf-8")
            print(f"Extracted resume text: {output_path}")
        else:
            print(text)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
