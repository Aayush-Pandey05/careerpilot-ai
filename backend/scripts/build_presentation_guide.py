"""Build a printable study guide from its maintained Markdown source."""

import re
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer


def main():
    root = Path(__file__).resolve().parents[2]
    source = (root / "docs/PRESENTATION_GUIDE.md").read_text(encoding="utf-8")
    output = root / "docs/CareerPilot_AI_Presentation_Guide.pdf"
    styles = {
        "title": ParagraphStyle(
            "Title", fontName="Times-Roman", fontSize=36, leading=42, textColor=colors.black, spaceAfter=16
        ),
        "heading": ParagraphStyle(
            "Heading", fontName="Times-Roman", fontSize=25, leading=30, textColor=colors.black, spaceAfter=23
        ),
        "body": ParagraphStyle(
            "Body",
            fontName="Helvetica",
            fontSize=10.5,
            leading=16.5,
            alignment=TA_LEFT,
            spaceAfter=14,
            textColor=colors.HexColor("#343434"),
        ),
        "label": ParagraphStyle(
            "Label",
            fontName="Courier",
            fontSize=8,
            leading=12,
            textColor=colors.HexColor("#777777"),
            spaceAfter=16,
        ),
        "toc": ParagraphStyle(
            "Contents",
            fontName="Helvetica",
            fontSize=9,
            leading=17,
            textColor=colors.HexColor("#555555"),
            spaceAfter=1,
        ),
    }
    story = [
        Paragraph("CAREERPILOT AI / STUDENT REFERENCE", styles["label"]),
        Paragraph("CareerPilot AI", styles["title"]),
        Paragraph("Presentation and viva guide", styles["heading"]),
    ]
    parts = re.split(r"^## ", source, flags=re.M)
    intro = "\n".join(parts[0].splitlines()[1:]).strip()
    for p in intro.split("\n\n"):
        story.append(Paragraph(escape(p).replace("\n", " "), styles["body"]))
    story.extend([Spacer(1, 10), Paragraph("READING MAP", styles["label"])])
    headings = [part.split("\n", 1)[0] for part in parts[1:]]
    for i, heading in enumerate(headings, 2):
        story.append(Paragraph(f'{escape(heading)} <font color="#999999"> / {i}</font>', styles["toc"]))
    for section in parts[1:]:
        heading, body = section.split("\n", 1)
        story.extend(
            [
                PageBreak(),
                Paragraph("CAREERPILOT AI / PRESENTATION GUIDE", styles["label"]),
                Paragraph(escape(heading), styles["heading"]),
            ]
        )
        for paragraph in body.strip().split("\n\n"):
            story.append(Paragraph(escape(paragraph).replace("\n", " "), styles["body"]))

    def footer(canvas, doc):
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#999999"))
        canvas.drawString(52, 30, "CareerPilot AI  |  Workflow, agents and explanation")
        canvas.drawRightString(543, 30, f"{doc.page}")

    doc = SimpleDocTemplate(
        str(output),
        pagesize=(595, 842),
        topMargin=47,
        bottomMargin=49,
        leftMargin=52,
        rightMargin=52,
        title="CareerPilot AI presentation and viva guide",
        author="CareerPilot AI",
    )
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(output)


if __name__ == "__main__":
    main()
