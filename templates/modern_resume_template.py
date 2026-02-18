#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Modern resume PDF template for resume-tailor skill."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

from reportlab.lib import colors
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

from templates.layout_settings import DEFAULT_SETTINGS, LayoutSettings


def register_fonts() -> tuple[str, str, str]:
    """Register Calibri with priority, fallback to Helvetica if failed."""
    try:
        calibri = Path(r"C:\Windows\Fonts\calibri.ttf")
        calibri_bold = Path(r"C:\Windows\Fonts\calibrib.ttf")
        calibri_italic = Path(r"C:\Windows\Fonts\calibrii.ttf")

        if calibri.exists() and calibri_bold.exists() and calibri_italic.exists():
            pdfmetrics.registerFont(TTFont("Calibri", str(calibri)))
            pdfmetrics.registerFont(TTFont("Calibri-Bold", str(calibri_bold)))
            pdfmetrics.registerFont(TTFont("Calibri-Italic", str(calibri_italic)))
            pdfmetrics.registerFontFamily(
                "Calibri",
                normal="Calibri",
                bold="Calibri-Bold",
                italic="Calibri-Italic",
                boldItalic="Calibri-Bold",
            )
            return "Calibri", "Calibri-Bold", "Calibri-Italic"
    except Exception:
        pass

    return "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"


def create_styles(
    base_font: str, bold_font: str, layout: LayoutSettings | None = None
) -> dict[str, ParagraphStyle]:
    """Create resume layout styles."""
    settings = layout or DEFAULT_SETTINGS
    fs = settings.effective_font_size_scale
    lh = settings.effective_line_height_scale
    ss = settings.effective_section_spacing_scale
    item_scale = settings.effective_item_spacing_scale

    styles = getSampleStyleSheet()

    custom_styles: dict[str, ParagraphStyle] = {}

    custom_styles["Header"] = ParagraphStyle(
        "Header",
        parent=styles["Normal"],
        fontSize=15 * fs,
        textColor=colors.black,
        spaceAfter=9 * ss,
        alignment=TA_CENTER,
        fontName=bold_font,
    )

    custom_styles["Contact"] = ParagraphStyle(
        "Contact",
        parent=styles["Normal"],
        fontSize=10.5 * fs,
        spaceAfter=11 * ss,
        alignment=TA_CENTER,
        fontName=base_font,
    )

    custom_styles["Section"] = ParagraphStyle(
        "Section",
        parent=styles["Normal"],
        fontSize=10.6 * fs,
        textColor=colors.black,
        spaceBefore=8.5 * ss,
        spaceAfter=5 * ss,
        fontName=bold_font,
        leading=13 * lh,
    )

    custom_styles["Body"] = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=9.85 * fs,
        leading=12.2 * lh,
        spaceAfter=6.2 * item_scale,
        alignment=TA_JUSTIFY,
        fontName=base_font,
    )

    custom_styles["CompanyTitle"] = ParagraphStyle(
        "CompanyTitle",
        parent=styles["Normal"],
        fontSize=9.9 * fs,
        leading=12 * lh,
        spaceAfter=4.5 * item_scale,
        fontName=base_font,
    )

    custom_styles["CompanyName"] = ParagraphStyle(
        "CompanyName",
        parent=styles["Normal"],
        fontSize=10.2 * fs,
        leading=12.5 * lh,
        spaceAfter=2.5 * item_scale,
        fontName=bold_font,
        alignment=TA_LEFT,
    )

    custom_styles["DatesRight"] = ParagraphStyle(
        "DatesRight",
        parent=styles["Normal"],
        fontSize=9.9 * fs,
        leading=12 * lh,
        fontName=base_font,
        alignment=TA_RIGHT,
    )

    custom_styles["JobDetail"] = ParagraphStyle(
        "JobDetail",
        parent=styles["Normal"],
        fontSize=9.9 * fs,
        leading=12 * lh,
        spaceAfter=4.5 * item_scale,
        fontName=base_font,
        alignment=TA_LEFT,
    )

    custom_styles["Bullet"] = ParagraphStyle(
        "Bullet",
        parent=styles["Normal"],
        fontSize=9.85 * fs,
        leading=12.2 * lh,
        leftIndent=15,
        spaceAfter=3.2 * item_scale,
        bulletIndent=5,
        fontName=base_font,
        alignment=TA_LEFT,
    )

    custom_styles["Education"] = ParagraphStyle(
        "Education",
        parent=styles["Normal"],
        fontSize=9.9 * fs,
        leading=12 * lh,
        spaceAfter=3.5 * item_scale,
        fontName=base_font,
    )

    custom_styles["EducationDegree"] = ParagraphStyle(
        "EducationDegree",
        parent=styles["Normal"],
        fontSize=9.9 * fs,
        leading=12 * lh,
        spaceAfter=3.5 * item_scale,
        fontName=base_font,
        alignment=TA_LEFT,
    )

    return custom_styles


def validate_content(content_dict: dict[str, Any]) -> None:
    required = ("name", "contact", "summary", "skills", "experience", "education")
    missing = [key for key in required if key not in content_dict]
    if missing:
        raise ValueError(f"Content missing required fields: {', '.join(missing)}")

    if not isinstance(content_dict["skills"], list):
        raise ValueError("`skills` must be an array.")
    if not isinstance(content_dict["experience"], list):
        raise ValueError("`experience` must be an array.")
    if not isinstance(content_dict["education"], list):
        raise ValueError("`education` must be an array.")


def infer_position_from_filename(output_name: str) -> str:
    """
    Infer position type from filename.
    Naming convention: {MM}_{DD}_{Name}_{Position}_resume.pdf
    """
    stem = Path(output_name).stem
    if not stem.endswith("_resume"):
        return "Uncategorized"

    core = stem[: -len("_resume")]
    parts = core.split("_")
    if len(parts) < 4:
        return "Uncategorized"

    position = "_".join(parts[3:]).strip("_")
    return position or "Uncategorized"


def get_next_backup_path(backup_dir: Path, output_stem: str) -> Path:
    pattern = re.compile(rf"^{re.escape(output_stem)}_old_(\d+)\.pdf$", re.IGNORECASE)
    max_number = 0

    for file in backup_dir.glob(f"{output_stem}_old_*.pdf"):
        match = pattern.match(file.name)
        if match:
            max_number = max(max_number, int(match.group(1)))

    return backup_dir / f"{output_stem}_old_{max_number + 1}.pdf"


def archive_root_pdfs(
    base_output_dir: Path, exclude_names: set[str] | None = None
) -> list[Path]:
    """Move historical PDFs from output root directory to backup directory."""
    excluded = exclude_names or set()
    archived_paths: list[Path] = []

    for pdf_file in sorted(base_output_dir.glob("*.pdf")):
        if pdf_file.name in excluded:
            continue

        position = infer_position_from_filename(pdf_file.name)
        backup_dir = base_output_dir / "backup" / position
        backup_dir.mkdir(parents=True, exist_ok=True)

        backup_path = get_next_backup_path(backup_dir, pdf_file.stem)
        pdf_file.replace(backup_path)
        archived_paths.append(backup_path)
        print(f"✓ Old file backed up to: {backup_path}")

    return archived_paths


def generate_resume(
    output_file: str,
    content_dict: dict[str, Any],
    base_dir: str = "resume_output",
    layout: LayoutSettings | None = None,
) -> str:
    """Generate resume PDF from structured content."""
    output_name = Path(output_file).name
    if output_name != output_file:
        raise ValueError("output_file must be filename only, cannot contain path.")

    validate_content(content_dict)

    base_output_dir = Path(base_dir)
    base_output_dir.mkdir(parents=True, exist_ok=True)

    output_path = base_output_dir / output_name
    output_stem = output_path.stem
    temp_output_path = base_output_dir / f".{output_stem}.tmp.pdf"

    if temp_output_path.exists():
        temp_output_path.unlink()

    settings = layout or DEFAULT_SETTINGS

    base_font, bold_font, _ = register_fonts()
    styles = create_styles(base_font, bold_font, layout=settings)

    doc = SimpleDocTemplate(
        str(temp_output_path),
        pagesize=A4,
        topMargin=settings.margin_top_mm * mm,
        bottomMargin=settings.margin_bottom_mm * mm,
        leftMargin=settings.margin_side_inch * inch,
        rightMargin=settings.margin_side_inch * inch,
    )

    story = []

    story.append(Paragraph(content_dict["name"], styles["Header"]))
    story.append(Paragraph(content_dict["contact"], styles["Contact"]))

    story.append(Paragraph("SUMMARY", styles["Section"]))
    story.append(
        HRFlowable(width="100%", thickness=1, color=colors.black, spaceAfter=4)
    )
    story.append(Paragraph(content_dict["summary"], styles["Body"]))

    story.append(Paragraph("TECHNICAL SKILLS", styles["Section"]))
    story.append(
        HRFlowable(width="100%", thickness=1, color=colors.black, spaceAfter=4)
    )
    for skill in content_dict["skills"]:
        category = skill.get("category", "Skill")
        items = skill.get("items", "")
        story.append(Paragraph(f"<b>{category}:</b> {items}", styles["Body"]))

    story.append(Paragraph("PROFESSIONAL EXPERIENCE", styles["Section"]))
    story.append(
        HRFlowable(width="100%", thickness=1, color=colors.black, spaceAfter=4)
    )

    for index, job in enumerate(content_dict["experience"]):
        company = job.get("company", "")
        title = job.get("title", "")
        location = job.get("location", "")
        dates = job.get("dates", "")
        bullets = job.get("bullets", [])

        company_dates_row = Table(
            [
                [
                    Paragraph(company, styles["CompanyName"]),
                    Paragraph(dates, styles["DatesRight"]),
                ]
            ],
            colWidths=[doc.width * 0.72, doc.width * 0.28],
        )
        company_dates_row.setStyle(
            TableStyle(
                [
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.append(company_dates_row)

        detail_parts = [part for part in (title, location) if part]
        detail_line = " | ".join(detail_parts)
        if detail_line:
            story.append(Paragraph(detail_line, styles["JobDetail"]))

        for bullet in bullets:
            story.append(Paragraph(f"• {bullet}", styles["Bullet"]))

        if index < len(content_dict["experience"]) - 1:
            story.append(Spacer(1, 0.05 * inch * settings.effective_item_spacing_scale))

    if content_dict.get("projects"):
        story.append(Paragraph("PROJECTS", styles["Section"]))
        story.append(
            HRFlowable(width="100%", thickness=1, color=colors.black, spaceAfter=4)
        )

        for index, project in enumerate(content_dict["projects"]):
            name = project.get("name", "")
            tech = project.get("tech", "")
            dates = project.get("dates", "")
            bullets = project.get("bullets", [])

            left_text = f"<b>{name}</b>"
            if tech:
                left_text += f" | {tech}"

            project_row = Table(
                [
                    [
                        Paragraph(left_text, styles["CompanyName"]),
                        Paragraph(dates, styles["DatesRight"]),
                    ]
                ],
                colWidths=[doc.width * 0.72, doc.width * 0.28],
            )
            project_row.setStyle(
                TableStyle(
                    [
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ]
                )
            )
            story.append(project_row)

            for bullet in bullets:
                story.append(Paragraph(f"• {bullet}", styles["Bullet"]))

            if index < len(content_dict["projects"]) - 1:
                story.append(
                    Spacer(1, 0.05 * inch * settings.effective_item_spacing_scale)
                )

    if content_dict.get("certifications"):
        story.append(Paragraph("CERTIFICATIONS", styles["Section"]))
        story.append(
            HRFlowable(width="100%", thickness=1, color=colors.black, spaceAfter=4)
        )
        for cert in content_dict["certifications"]:
            name = cert.get("name", "")
            issuer = cert.get("issuer", "")
            dates = cert.get("dates", "")
            left_text = f"<b>{name}</b>"
            if issuer:
                left_text += f" - {issuer}"

            cert_row = Table(
                [
                    [
                        Paragraph(left_text, styles["Education"]),
                        Paragraph(dates, styles["DatesRight"]),
                    ]
                ],
                colWidths=[doc.width * 0.72, doc.width * 0.28],
            )
            cert_row.setStyle(
                TableStyle(
                    [
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ]
                )
            )
            story.append(cert_row)

    if content_dict.get("awards"):
        story.append(Paragraph("AWARDS", styles["Section"]))
        story.append(
            HRFlowable(width="100%", thickness=1, color=colors.black, spaceAfter=4)
        )
        for award in content_dict["awards"]:
            name = award.get("name", "")
            organization = award.get("organization", "")
            dates = award.get("dates", "")
            left_text = f"<b>{name}</b>"
            if organization:
                left_text += f" - {organization}"

            award_row = Table(
                [
                    [
                        Paragraph(left_text, styles["Education"]),
                        Paragraph(dates, styles["DatesRight"]),
                    ]
                ],
                colWidths=[doc.width * 0.72, doc.width * 0.28],
            )
            award_row.setStyle(
                TableStyle(
                    [
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ]
                )
            )
            story.append(award_row)

    story.append(Paragraph("EDUCATION", styles["Section"]))
    story.append(
        HRFlowable(width="100%", thickness=1, color=colors.black, spaceAfter=4)
    )

    for edu in content_dict["education"]:
        school = edu.get("school", "")
        degree = edu.get("degree", "")
        dates = edu.get("dates", "")

        school_dates_row = Table(
            [
                [
                    Paragraph(f"<b>{school}</b>", styles["Education"]),
                    Paragraph(dates, styles["DatesRight"]),
                ]
            ],
            colWidths=[doc.width * 0.72, doc.width * 0.28],
        )
        school_dates_row.setStyle(
            TableStyle(
                [
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.append(school_dates_row)

        if degree:
            story.append(Paragraph(degree, styles["EducationDegree"]))

    doc.build(story)

    archive_root_pdfs(base_output_dir, exclude_names={temp_output_path.name})
    temp_output_path.replace(output_path)

    print(f"✓ PDF generation completed: {output_path}")
    print(f"✓ Font used: {base_font}")
    return str(output_path)


if __name__ == "__main__":
    example_content = {
        "name": "FULL NAME",
        "contact": "City, State • +1 000-000-0000 • email@example.com • linkedin.com/in/your-id",
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
