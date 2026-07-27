from datetime import datetime

from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def create_pdf_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="MainTitle", parent=styles["Title"], alignment=TA_CENTER, fontSize=24, textColor=HexColor("#2563EB"), spaceAfter=6))
    styles.add(ParagraphStyle(name="SubTitle", parent=styles["Heading2"], alignment=TA_CENTER, fontSize=13, textColor=HexColor("#6B7280"), spaceAfter=20))
    styles.add(ParagraphStyle(name="SectionHeading", parent=styles["Heading2"], fontSize=15, textColor=HexColor("#1D4ED8"), spaceBefore=15, spaceAfter=10))
    styles.add(ParagraphStyle(name="ScoreStyle", parent=styles["Title"], alignment=TA_CENTER, fontSize=34, textColor=HexColor("#059669"), spaceAfter=10))
    return styles


def add_header(story, styles, report):
    story.append(Paragraph("<b>ResumePilot AI</b>", styles["MainTitle"]))
    story.append(Paragraph("Professional ATS Analysis Report", styles["SubTitle"]))
    story.append(Spacer(1, 15))
    story.append(Paragraph(f"<b>Resume:</b> {report['resume_name']}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Generated On:</b> {datetime.now().strftime('%d %B %Y | %I:%M %p')}", styles["BodyText"]))
    story.append(Spacer(1, 20))


def create_progress_bar(score, width=250, height=14):
    drawing = Drawing(width, height + 15)
    drawing.add(Rect(0, 0, width, height, strokeColor=colors.grey, fillColor=colors.whitesmoke))
    bar_color = colors.green if score >= 80 else colors.orange if score >= 60 else colors.red
    drawing.add(Rect(0, 0, width * score / 100, height, fillColor=bar_color, strokeColor=bar_color))
    drawing.add(String(width + 10, 2, f"{score:.0f}%"))
    return drawing


def add_score_card(story, styles, report):
    story.append(Paragraph("<b>ATS SCORE</b>", styles["SectionHeading"]))
    story.append(Paragraph(f"<b>{report['score']}%</b>", styles["ScoreStyle"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph(report["overall_assessment"]["title"], styles["SectionHeading"]))
    story.append(create_progress_bar(report["score"]))
    story.append(Spacer(1, 15))
    story.append(Paragraph(report["overall_assessment"]["message"], styles["BodyText"]))
    story.append(Spacer(1, 20))


def _table_style(header_color, body_color=colors.whitesmoke):
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), header_color), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("BACKGROUND", (0, 1), (-1, -1), body_color),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey), ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10), ("TOPPADDING", (0, 1), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 8),
    ])


def add_score_table(story, styles, report):
    story.append(Paragraph("<b>Score Breakdown</b>", styles["SectionHeading"]))
    data = [["Metric", "Score"], ["ATS Score", f"{report['score']}%"], ["Section Score", f"{report['section_score']}%"], ["Contact Score", f"{report['contact_score']}%"], ["Completeness Score", f"{report['completeness_score']}%"]]
    table = Table(data, colWidths=[4 * inch, 1.5 * inch])
    table.setStyle(_table_style(colors.HexColor("#2563EB")))
    story.append(table)
    story.append(Spacer(1, 20))


def add_resume_health(story, styles, report):
    story.append(Paragraph("<b>Resume Health</b>", styles["SectionHeading"]))
    data = [["Section", "Status"]]
    data.extend([section, "âœ” Present" if present else "âœ– Missing"] for section, present in report["sections"].items())
    table = Table(data, colWidths=[4 * inch, 2 * inch])
    table.setStyle(_table_style(colors.HexColor("#2563EB")))
    story.append(table)
    story.append(Spacer(1, 20))


def add_contact_section(story, styles, report):
    story.append(Paragraph("<b>Contact Information</b>", styles["SectionHeading"]))
    data = [["Contact", "Status"]]
    data.extend([contact, "âœ” Available" if present else "âœ– Missing"] for contact, present in report["contact"].items())
    table = Table(data, colWidths=[4 * inch, 2 * inch])
    table.setStyle(_table_style(colors.HexColor("#2563EB")))
    story.append(table)
    story.append(Spacer(1, 20))


def add_skills_section(story, styles, report):
    story.append(Paragraph("<b>Detected Skills</b>", styles["SectionHeading"]))
    skills = report["resume_skills"]
    if not skills:
        story.append(Paragraph("No technical skills detected.", styles["BodyText"]))
        story.append(Spacer(1, 20))
        return
    data = [["Skill", "Skill"]]
    for i in range(0, len(skills), 2):
        data.append([skills[i], skills[i + 1] if i + 1 < len(skills) else ""])
    table = Table(data, colWidths=[3 * inch, 3 * inch])
    table.setStyle(_table_style(colors.HexColor("#2563EB")))
    story.append(table)
    story.append(Spacer(1, 20))


def _add_suggestions_table(story, styles, heading, header, items, header_color, body_color, marker):
    story.append(Paragraph(f"<b>{heading}</b>", styles["SectionHeading"]))
    data = [[header]]
    data.extend([f"{marker} {item}"] for item in items)
    table = Table(data, colWidths=[6 * inch])
    table.setStyle(_table_style(header_color, body_color))
    table.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12)]))
    story.append(table)
    story.append(Spacer(1, 20))


def add_recommendations(story, styles, report):
    _add_suggestions_table(story, styles, "Recommendations", "Suggestions", report["recommendations"], colors.HexColor("#F59E0B"), colors.HexColor("#FEF3C7"), "âœ“")


def add_footer(story, styles):
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>Generated by ResumePilot AI</b>", styles["SectionHeading"]))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%d %B %Y | %I:%M %p')}", styles["BodyText"]))
    story.append(Paragraph("Thank you for using ResumePilot AI. Best of luck with your career!", styles["BodyText"]))


def add_page_border(canvas, doc):
    canvas.saveState()
    width, height = doc.pagesize
    margin = 20
    canvas.setStrokeColor(colors.HexColor("#2563EB"))
    canvas.setLineWidth(2)
    canvas.rect(margin, margin, width - 2 * margin, height - 2 * margin)
    canvas.restoreState()


def add_matched_skills(story, styles, report):
    skills = report["matched_skills"] or ["No matched skills found."]
    _add_suggestions_table(story, styles, "Matched Skills", "Matched Skills", skills, colors.HexColor("#16A34A"), colors.HexColor("#DCFCE7"), "âœ“")


def add_missing_skills(story, styles, report):
    skills = report["missing_skills"] or ["Excellent! No missing skills."]
    _add_suggestions_table(story, styles, "Missing Skills", "Missing Skills", skills, colors.HexColor("#DC2626"), colors.HexColor("#FEE2E2"), "âœ—")


def add_job_match_feedback(story, styles, report):
    _add_suggestions_table(story, styles, "Improvement Suggestions", "Suggestions", report["feedback"], colors.HexColor("#F59E0B"), colors.HexColor("#FEF3C7"), "âœ“")


def build_pdf_report(buffer, report):
    doc = SimpleDocTemplate(buffer)
    styles = create_pdf_styles()
    story = []
    add_header(story, styles, report)
    # The original report card expects an assessment only in analysis mode.
    if report.get("mode") == "job_match":
        # Preserve the historical job-match layout, which omits the analysis-only card.
        story.append(Paragraph("<b>ATS SCORE</b>", styles["SectionHeading"]))
        story.append(Paragraph(f"<b>{report['score']}%</b>", styles["ScoreStyle"]))
        story.append(create_progress_bar(report["score"]))
        story.append(Spacer(1, 20))
    else:
        add_score_card(story, styles, report)
    add_score_table(story, styles, report)
    if report.get("mode") == "job_match":
        add_matched_skills(story, styles, report)
        add_missing_skills(story, styles, report)
        add_job_match_feedback(story, styles, report)
    else:
        add_resume_health(story, styles, report)
        add_contact_section(story, styles, report)
        add_skills_section(story, styles, report)
        add_recommendations(story, styles, report)
    add_footer(story, styles)
    doc.build(story, onFirstPage=add_page_border, onLaterPages=add_page_border)
