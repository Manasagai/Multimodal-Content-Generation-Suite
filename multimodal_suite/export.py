"""PDF export helpers."""
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from xml.sax.saxutils import escape
import json

def export_campaign_to_pdf(campaign):
    out_dir = Path(__file__).resolve().parents[1] / "exports"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"campaign_{campaign.id}.pdf"
    styles = getSampleStyleSheet()
    story = [Paragraph(escape(campaign.name), styles["Title"]), Spacer(1, 12)]
    if campaign.description:
        story += [Paragraph("Product description", styles["Heading2"]),
                  Paragraph(escape(campaign.description), styles["BodyText"]), Spacer(1, 10)]
    try:
        brief = json.loads(campaign.brief or "{}")
    except Exception:
        brief = {}
    if isinstance(brief, dict):
        for key, value in brief.items():
            story.append(Paragraph(escape(str(key).replace("_", " ").title()), styles["Heading3"]))
            if isinstance(value, list):
                text = "<br/>".join(escape(str(item)) for item in value)
            else:
                text = escape(str(value))
            story.append(Paragraph(text or "-", styles["BodyText"]))
            story.append(Spacer(1, 7))
    SimpleDocTemplate(str(path), pagesize=A4).build(story)
    return str(path)
