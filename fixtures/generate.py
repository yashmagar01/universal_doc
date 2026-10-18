"""Deterministic synthetic fixture PDFs for Templix dev + e2e (dev-only; never shipped).

Run:  uv run python fixtures/generate.py     (from apps/server, or via scripts/fixtures.ps1)
Out:  fixtures/generated/*.pdf + manifest.json

Fixtures are the sanctioned source of demo data (docs/decisions.md OQ-2). No real files.
"""

from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

OUT = Path(__file__).resolve().parent / "generated"
W, H = LETTER  # 612 x 792 pt


def _masthead(c: canvas.Canvas, title: str, kicker: str) -> None:
    c.setFont("Helvetica-Bold", 30)
    c.drawString(48, H - 88, title)
    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0.04, 0.4, 0.76)
    c.drawString(48, H - 108, kicker)
    c.setStrokeColorRGB(0.04, 0.4, 0.76)
    c.setLineWidth(1.5)
    c.line(48, H - 116, W - 48, H - 116)
    c.setFillColorRGB(0, 0, 0)


def _footer(c: canvas.Canvas, page: int, pages: int, label: str) -> None:
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawString(48, 32, label)
    c.drawRightString(W - 48, 32, f"Page {page} of {pages}")
    c.setFillColorRGB(0, 0, 0)


def _body(c: canvas.Canvas, x: float, y: float, width: float, lines: list[str], size: int = 10, leading: int = 13) -> float:
    c.setFont("Helvetica", size)
    for line in lines:
        if y < 60:
            break
        c.drawString(x, y, line)
        y -= leading
    return y


LOREM = [
    "University administration has officially ratified the digital privacy initiative,",
    "dedicating campus nodes strictly to private local processing. Students working on",
    "sensitive research theses and institutional datasets can now execute extraction",
    "routines without external dependencies. Regular training orientations take place",
    "Tuesdays and Thursdays in Hall C. Templates created locally are fully exportable",
    "to standard document specifications, making formatting updates instantaneous.",
]


def newsletter_2col(path: Path) -> dict:
    c = canvas.Canvas(str(path), pagesize=LETTER)
    pages = 2
    _masthead(c, "CAMPUS CHRONICLE", "STUDENT AFFAIRS & LEADERSHIP BRIEFING - March 2025 - Vol. 14 - Issue 4")
    c.setFont("Helvetica-Bold", 17)
    c.drawString(48, H - 160, "New Local AI Laboratories Open for Collaborative")
    c.drawString(48, H - 180, "Research Projects")
    c.setFillColorRGB(0.04, 0.4, 0.76)
    c.rect(48, H - 360, 246, 150, stroke=0, fill=1)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica", 8)
    c.drawCentredString(48 + 123, H - 255, "[Story Photo - Students at the laboratory]")
    c.setFillColorRGB(0.04, 0.4, 0.76)
    c.rect(310, H - 360, 254, 150, stroke=0, fill=1)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(310 + 127, H - 280, "Callout quote:")
    c.drawCentredString(310 + 127, H - 296, "Empowering student voices through")
    c.drawCentredString(310 + 127, H - 312, "private local infrastructure.")
    c.setFillColorRGB(0, 0, 0)
    _body(c, 48, H - 388, 246, LOREM)
    _body(c, 310, H - 388, 254, LOREM[:5])
    _footer(c, 1, pages, "Campus Chronicle - Student Affairs Publication Office")
    c.showPage()
    _masthead(c, "CAMPUS CHRONICLE", "STUDENT AFFAIRS & LEADERSHIP BRIEFING - March 2025 - Vol. 14 - Issue 4")
    c.setFont("Helvetica-Bold", 14)
    c.drawString(48, H - 150, "This Week on Campus")
    _body(c, 48, H - 176, 516, LOREM * 2)
    _footer(c, 2, pages, "Campus Chronicle - Student Affairs Publication Office")
    c.showPage()
    c.save()
    return {"file": path.name, "pages": pages, "kind": "newsletter", "expectLayers": 12}


def report_6page(path: Path) -> dict:
    c = canvas.Canvas(str(path), pagesize=LETTER)
    pages = 6
    c.setFont("Helvetica-Bold", 26)
    c.drawString(48, H - 120, "Annual Financial & Activities Report")
    c.setFont("Helvetica", 12)
    c.drawString(48, H - 150, "Fiscal Year 2024-25 - Student Publishing Board")
    _footer(c, 1, pages, "Annual Report")
    c.showPage()
    for p in range(2, pages + 1):
        c.setFont("Helvetica-Bold", 16)
        c.drawString(48, H - 88, f"Section {p - 1}: Departmental Summary")
        c.setFont("Helvetica", 10)
        for row in range(14):
            c.drawString(48, H - 120 - row * 22, f"Line {row + 1:02d} - description of budget activity item for the reporting period")
            c.drawRightString(W - 48, H - 120 - row * 22, f"{(row + 1) * 1375:,.2f}")
        _footer(c, p, pages, "Annual Report")
        c.showPage()
    c.save()
    return {"file": path.name, "pages": pages, "kind": "report", "expectLayers": 18}


def exec_weekly_1page(path: Path) -> dict:
    c = canvas.Canvas(str(path), pagesize=LETTER)
    _masthead(c, "EXECUTIVE COMMITTEE WEEKLY", "Week 14 - Decisions & Actions")
    c.setFont("Helvetica-Bold", 13)
    c.drawString(48, H - 150, "Decisions")
    _body(c, 48, H - 172, 516, [
        "1. Approved the local-first tooling budget for the next two quarters.",
        "2. Deferred the archives migration pending storage review.",
    ])
    c.setFont("Helvetica-Bold", 13)
    c.drawString(48, H - 230, "Action Items")
    _body(c, 48, H - 252, 516, [
        "- S. Iyer: publish the March newsletter by the 28th.",
        "- M. Chen: brief the new laboratory cohort on template usage.",
    ])
    _footer(c, 1, 1, "Executive Committee Weekly")
    c.showPage()
    c.save()
    return {"file": path.name, "pages": 1, "kind": "newsletter", "expectLayers": 8}


def orientation_3page(path: Path) -> dict:
    c = canvas.Canvas(str(path), pagesize=LETTER)
    pages = 3
    c.setFont("Helvetica-Bold", 28)
    c.drawString(48, H - 120, "Orientation Week Guide & Map")
    c.setFont("Helvetica", 11)
    c.drawString(48, H - 150, "Welcome to campus - everything you need in one place")
    c.setFillColorRGB(0.1, 0.6, 0.3)
    c.rect(48, H - 420, 516, 220, stroke=0, fill=1)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(W / 2, H - 320, "[Campus Map - Buildings A through F]")
    c.setFillColorRGB(0, 0, 0)
    _footer(c, 1, pages, "Orientation Week")
    c.showPage()
    for p in (2, 3):
        c.setFont("Helvetica-Bold", 16)
        c.drawString(48, H - 88, f"Day {p} - Schedule")
        _body(c, 48, H - 116, 516, LOREM)
        _footer(c, p, pages, "Orientation Week")
        c.showPage()
    c.save()
    return {"file": path.name, "pages": pages, "kind": "flyer", "expectLayers": 15}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = [
        newsletter_2col(OUT / "newsletter_2col.pdf"),
        report_6page(OUT / "report_6page.pdf"),
        exec_weekly_1page(OUT / "exec_weekly_1page.pdf"),
        orientation_3page(OUT / "orientation_3page.pdf"),
    ]
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {len(manifest)} fixture PDFs to {OUT}")


if __name__ == "__main__":
    main()
