from html import escape
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def generate_report(analysis):
    output = BytesIO()
    doc = SimpleDocTemplate(
        output, pagesize=(595, 842), rightMargin=45, leftMargin=45, topMargin=45, bottomMargin=45
    )
    styles = getSampleStyleSheet()
    story = []

    def paragraph(text, style="BodyText"):
        story.append(Paragraph(escape(str(text)).replace("\n", "<br/>"), styles[style]))
        story.append(Spacer(1, 8))

    payload = analysis["result"]
    paragraph("CareerPilot AI", "Title")
    paragraph(f"{analysis['job_title']} | {analysis['company']}", "Heading2")
    paragraph(f"Mode: {payload.get('mode', 'unknown')} | Review: {analysis['workflow_status']}")
    paragraph(f"Candidate: {payload.get('resume', {}).get('candidate_name', 'Unknown')}")
    paragraph(
        f"Compatibility: {analysis['match_score'] if analysis['match_score'] is not None else 'Not scorable'}/100"
    )
    paragraph("This score describes resume compatibility. It is not a hiring probability.")
    rows = [[Paragraph(v, styles["BodyText"]) for v in ["Requirement", "Status", "Resume evidence"]]]
    for r in payload.get("matching", {}).get("requirements", []):
        rows.append(
            [
                Paragraph(escape(str(v)), styles["BodyText"])
                for v in [r["requirement"], r["status"], r["evidence"] or r["explanation"]]
            ]
        )
    table = Table(rows, colWidths=[1.55 * inch, 1.2 * inch, 4.25 * inch - 35], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ]
        )
    )
    story.extend([table, Spacer(1, 12)])
    application = payload.get("application", {})
    for title, value in [
        ("Recommendations", application.get("resume_suggestions", [])),
        ("Application email", application.get("email", "")),
        ("Cover letter", application.get("cover_letter", "")),
        ("Interview preparation", application.get("interview_questions", [])),
        ("Review issues", payload.get("review", {}).get("issues", [])),
    ]:
        paragraph(title, "Heading2")
        for item in value if isinstance(value, list) else [value]:
            paragraph(item)
    doc.build(story)
    return output.getvalue()
