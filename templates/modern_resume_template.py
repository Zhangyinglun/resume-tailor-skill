#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Modern resume PDF template for resume-tailor skill."""

from __future__ import annotations

import functools
import re
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.colors import Color
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from scripts.resume_shared import validate_resume_content
from templates.design_tokens import DEFAULT_TOKENS, DesignTokens
from templates.layout_settings import DEFAULT_SETTINGS, LayoutSettings

_TWO_COL_STYLE = TableStyle(
    [
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
)


def _colors_from_tokens(tokens: DesignTokens) -> tuple[Color, Color]:
    """Convert token RGB tuples to ReportLab Color objects."""
    ac = tokens.accent_color
    bi = tokens.body_ink_color
    return (
        Color(ac[0] / 255, ac[1] / 255, ac[2] / 255),
        Color(bi[0] / 255, bi[1] / 255, bi[2] / 255),
    )


def _two_col_row(left: Paragraph, right: Paragraph, width: float) -> Table:
    """Create a two-column Table row (72%/28%) with standard padding."""
    tbl = Table([[left, right]], colWidths=[width * 0.72, width * 0.28])
    tbl.setStyle(_TWO_COL_STYLE)
    return tbl


def _add_section(story: list, title: str, styles: dict[str, ParagraphStyle],
                  accent: Color, tokens: DesignTokens | None = None) -> None:
    """Append a section heading with horizontal rule."""
    t = tokens or DEFAULT_TOKENS
    story.append(Paragraph(title, styles["Section"]))
    story.append(HRFlowable(width="100%", thickness=t.section_hr_thickness, color=accent, spaceAfter=4))


@functools.lru_cache(maxsize=1)
def register_fonts() -> tuple[str, str, str]:
    """Register Calibri with priority, fallback to Helvetica if failed."""
    try:
        fonts = {
            "Calibri": Path(r"C:\Windows\Fonts\calibri.ttf"),
            "Calibri-Bold": Path(r"C:\Windows\Fonts\calibrib.ttf"),
            "Calibri-Italic": Path(r"C:\Windows\Fonts\calibrii.ttf"),
        }
        if all(p.exists() for p in fonts.values()):
            for name, path in fonts.items():
                pdfmetrics.registerFont(TTFont(name, str(path)))
            pdfmetrics.registerFontFamily(
                "Calibri", normal="Calibri", bold="Calibri-Bold",
                italic="Calibri-Italic", boldItalic="Calibri-Bold",
            )
            return "Calibri", "Calibri-Bold", "Calibri-Italic"
    except Exception:
        pass

    return "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"


def create_styles(
    base_font: str, bold_font: str,
    layout: LayoutSettings | None = None,
    tokens: DesignTokens | None = None,
) -> dict[str, ParagraphStyle]:
    """Create resume layout styles."""
    s = layout or DEFAULT_SETTINGS
    fs = s.effective_font_size_scale
    lh = s.effective_line_height_scale
    ss = s.effective_section_spacing_scale
    it = s.effective_item_spacing_scale

    t = tokens or DEFAULT_TOKENS
    accent, body_ink = _colors_from_tokens(t)

    parent = getSampleStyleSheet()["Normal"]

    def style(name: str, **kw: Any) -> ParagraphStyle:
        return ParagraphStyle(name, parent=parent, **kw)

    return {
        "Header": style("Header", fontSize=t.header_font_size*fs, leading=t.header_leading*lh,
                         textColor=body_ink, spaceAfter=t.header_space_after*ss,
                         alignment=TA_CENTER, fontName=bold_font),
        "Contact": style("Contact", fontSize=t.contact_font_size*fs, textColor=body_ink,
                          spaceAfter=t.contact_space_after*ss, alignment=TA_CENTER, fontName=base_font),
        "Section": style("Section", fontSize=t.section_font_size*fs, textColor=accent,
                          spaceBefore=t.section_space_before*ss, spaceAfter=t.section_space_after*ss,
                          fontName=bold_font, leading=t.section_leading*lh),
        "Body": style("Body", fontSize=t.body_font_size*fs, leading=t.body_leading*lh, textColor=body_ink,
                       spaceAfter=t.body_space_after*it, alignment=TA_JUSTIFY, fontName=base_font),
        "CompanyName": style("CompanyName", fontSize=t.company_font_size*fs, leading=t.company_leading*lh,
                              textColor=body_ink, spaceAfter=t.company_space_after*it,
                              fontName=bold_font, alignment=TA_LEFT),
        "DatesRight": style("DatesRight", fontSize=t.dates_font_size*fs, leading=t.dates_leading*lh,
                             textColor=body_ink, fontName=base_font, alignment=TA_RIGHT),
        "JobDetail": style("JobDetail", fontSize=t.job_detail_font_size*fs, leading=t.job_detail_leading*lh,
                            textColor=body_ink, spaceAfter=t.job_detail_space_after*it,
                            fontName=base_font, alignment=TA_LEFT),
        "Bullet": style("Bullet", fontSize=t.bullet_font_size*fs, leading=t.bullet_leading*lh,
                         textColor=body_ink, leftIndent=t.bullet_left_indent,
                         spaceAfter=t.bullet_space_after*it, bulletIndent=t.bullet_indent,
                         fontName=base_font, alignment=TA_LEFT),
        "Education": style("Education", fontSize=t.education_font_size*fs, leading=t.education_leading*lh,
                            textColor=body_ink, spaceAfter=t.education_space_after*it, fontName=base_font),
        "EducationDegree": style("EducationDegree", fontSize=t.education_font_size*fs,
                                  leading=t.education_leading*lh, textColor=body_ink,
                                  spaceAfter=t.education_space_after*it, fontName=base_font,
                                  alignment=TA_LEFT),
    }


def infer_position_from_filename(output_name: str) -> str:
    stem = Path(output_name).stem
    if not stem.endswith("_resume"):
        return "Uncategorized"
    parts = stem[: -len("_resume")].split("_")
    if len(parts) < 4:
        return "Uncategorized"
    return "_".join(parts[3:]).strip("_") or "Uncategorized"


def get_next_backup_path(backup_dir: Path, output_stem: str) -> Path:
    pattern = re.compile(rf"^{re.escape(output_stem)}_old_(\d+)\.pdf$", re.IGNORECASE)
    max_number = max(
        (int(m.group(1)) for f in backup_dir.glob(f"{output_stem}_old_*.pdf")
         if (m := pattern.match(f.name))),
        default=0,
    )
    return backup_dir / f"{output_stem}_old_{max_number + 1}.pdf"


def archive_root_pdfs(
    base_output_dir: Path, exclude_names: set[str] | None = None
) -> list[Path]:
    """Move historical PDFs from output root directory to backup directory."""
    excluded = exclude_names or set()
    archived: list[Path] = []

    for pdf_file in sorted(base_output_dir.glob("*.pdf")):
        if pdf_file.name in excluded:
            continue
        backup_dir = base_output_dir / "backup" / infer_position_from_filename(pdf_file.name)
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = get_next_backup_path(backup_dir, pdf_file.stem)
        pdf_file.replace(backup_path)
        archived.append(backup_path)
        print(f"\u2713 Old file backed up to: {backup_path}")

    return archived


def _render_two_col_items(
    story: list,
    items: list[dict[str, Any]],
    styles: dict[str, ParagraphStyle],
    doc_width: float,
    item_spacing: float,
    *,
    left_builder: Callable[[dict[str, Any]], str],
    dates_key: str = "dates",
    has_bullets: bool = True,
    detail_builder: Callable[[dict[str, Any]], str] | None = None,
) -> None:
    """Render a list of items with two-column header rows."""
    for i, item in enumerate(items):
        left_text = left_builder(item)
        story.append(_two_col_row(
            Paragraph(left_text, styles["CompanyName"]),
            Paragraph(item.get(dates_key, ""), styles["DatesRight"]),
            doc_width,
        ))
        if detail_builder:
            detail = detail_builder(item)
            if detail:
                story.append(Paragraph(detail, styles["JobDetail"]))
        if has_bullets:
            for bullet in item.get("bullets", []):
                story.append(Paragraph(f"\u2022 {bullet}", styles["Bullet"]))
        if i < len(items) - 1 and has_bullets:
            story.append(Spacer(1, 0.05 * inch * item_spacing))


def generate_resume(
    output_file: str,
    content_dict: dict[str, Any],
    base_dir: str = "resume_output",
    layout: LayoutSettings | None = None,
    tokens: DesignTokens | None = None,
) -> str:
    """Generate resume PDF from structured content."""
    output_name = Path(output_file).name
    if output_name != output_file:
        raise ValueError("output_file must be filename only, cannot contain path.")

    validate_resume_content(content_dict)

    base_output_dir = Path(base_dir)
    base_output_dir.mkdir(parents=True, exist_ok=True)

    output_path = base_output_dir / output_name
    temp_output_path = base_output_dir / f".{output_path.stem}.tmp.pdf"
    if temp_output_path.exists():
        temp_output_path.unlink()

    settings = layout or DEFAULT_SETTINGS
    t = tokens or DEFAULT_TOKENS
    accent, _body_ink = _colors_from_tokens(t)

    base_font, bold_font, _ = register_fonts()
    styles = create_styles(base_font, bold_font, layout=settings, tokens=t)

    doc = SimpleDocTemplate(
        str(temp_output_path),
        pagesize=A4,
        topMargin=settings.margin_top_mm * mm,
        bottomMargin=settings.margin_bottom_mm * mm,
        leftMargin=settings.margin_side_inch * inch,
        rightMargin=settings.margin_side_inch * inch,
    )

    story: list = []
    item_spacing = settings.effective_item_spacing_scale

    # Header — name, then contact
    story.append(Paragraph(content_dict["name"], styles["Header"]))
    story.append(Paragraph(content_dict["contact"], styles["Contact"]))

    # Summary
    _add_section(story, "SUMMARY", styles, accent, t)
    story.append(Paragraph(content_dict["summary"], styles["Body"]))

    # Experience
    _add_section(story, "PROFESSIONAL EXPERIENCE", styles, accent, t)
    _render_two_col_items(
        story, content_dict["experience"], styles, doc.width, item_spacing,
        left_builder=lambda j: j.get("company", ""),
        detail_builder=lambda j: " | ".join(p for p in (j.get("title", ""), j.get("location", "")) if p),
    )

    # Projects (optional)
    if content_dict.get("projects"):
        _add_section(story, "PROJECTS", styles, accent, t)
        _render_two_col_items(
            story, content_dict["projects"], styles, doc.width, item_spacing,
            left_builder=lambda p: f"<b>{p.get('name', '')}</b>" + (f" | {p['tech']}" if p.get("tech") else ""),
        )

    # Skills
    _add_section(story, "TECHNICAL SKILLS", styles, accent, t)
    for skill in content_dict["skills"]:
        story.append(Paragraph(
            f"<b>{skill.get('category', 'Skill')}:</b> {skill.get('items', '')}",
            styles["Body"],
        ))

    # Certifications (optional)
    if content_dict.get("certifications"):
        _add_section(story, "CERTIFICATIONS", styles, accent, t)
        _render_two_col_items(
            story, content_dict["certifications"], styles, doc.width, item_spacing,
            left_builder=lambda c: f"<b>{c.get('name', '')}</b>" + (f" - {c['issuer']}" if c.get("issuer") else ""),
            has_bullets=False,
        )

    # Awards (optional)
    if content_dict.get("awards"):
        _add_section(story, "AWARDS", styles, accent, t)
        _render_two_col_items(
            story, content_dict["awards"], styles, doc.width, item_spacing,
            left_builder=lambda a: f"<b>{a.get('name', '')}</b>" + (f" - {a['organization']}" if a.get("organization") else ""),
            has_bullets=False,
        )

    # Education
    _add_section(story, "EDUCATION", styles, accent, t)
    for edu in content_dict["education"]:
        story.append(_two_col_row(
            Paragraph(f"<b>{edu.get('school', '')}</b>", styles["Education"]),
            Paragraph(edu.get("dates", ""), styles["DatesRight"]),
            doc.width,
        ))
        if edu.get("degree"):
            story.append(Paragraph(edu["degree"], styles["EducationDegree"]))

    doc.build(story)

    archive_root_pdfs(base_output_dir, exclude_names={temp_output_path.name})
    temp_output_path.replace(output_path)

    print(f"\u2713 PDF generation completed: {output_path}")
    print(f"\u2713 Font used: {base_font}")
    return str(output_path)


if __name__ == "__main__":
    example_content = {
        "name": "FULL NAME",
        "contact": "City, State \u2022 +1 000-000-0000 \u2022 email@example.com \u2022 linkedin.com/in/your-id",
        "summary": "Experienced engineer with strengths in distributed systems and data platforms.",
        "skills": [
            {"category": "Programming Languages", "items": "Python, Go, Java"},
            {"category": "Data Platform", "items": "Kafka, Spark, Hadoop"},
        ],
        "experience": [
            {
                "company": "Example Corp",
                "title": "Software Engineer",
                "location": "Seattle, WA",
                "dates": "2023 - Present",
                "bullets": [
                    "Built a streaming pipeline and reduced data latency by 35%.",
                    "Improved service reliability to 99.95% through automated failover.",
                ],
            }
        ],
        "education": [
            {
                "school": "Example University",
                "degree": "M.S. in Computer Science",
                "dates": "2021 - 2023",
            }
        ],
    }

    output_name = sys.argv[1] if len(sys.argv) > 1 else "resume_example.pdf"
    generate_resume(output_name, example_content, base_dir="resume_output/test")
