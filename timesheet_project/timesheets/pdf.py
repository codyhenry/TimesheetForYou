from decimal import Decimal
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import TimeEntry


def _signature_cell(entry, styles):
    if entry.signature_status == TimeEntry.SignatureStatus.SIGNED and hasattr(entry, "parent_signature"):
        image_field = entry.parent_signature.image
        try:
            image_path = Path(image_field.path)
            if image_path.exists():
                return Image(str(image_path), width=1.3 * inch, height=0.45 * inch)
        except Exception:
            pass
        return Paragraph("SIGNED", styles["BodyText"])
    return Paragraph('<font color="red">UNSIGNED</font>', styles["BodyText"])


def render_timesheet_pdf(timesheet):
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer, pagesize=LETTER, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=24)
    styles = getSampleStyleSheet()
    entries = list(timesheet.entries.select_related("parent_signature").all())

    total_hours = sum(
        (entry.total_hours for entry in entries), Decimal("0.00"))
    signed_count = sum(
        1 for entry in entries if entry.signature_status == TimeEntry.SignatureStatus.SIGNED)
    unsigned_count = len(entries) - signed_count

    story = [
        Paragraph("TimesheetForYou", styles["Title"]),
        Spacer(1, 0.15 * inch),
        Paragraph(
            f"Nanny: {timesheet.nanny.get_full_name() or timesheet.nanny.username}", styles["Normal"]),
        Paragraph(
            f"Week: {timesheet.week_start_date} to {timesheet.week_end_date}", styles["Normal"]),
        Paragraph(
            f"Submitted: {timesheet.submitted_at.isoformat(sep=' ', timespec='seconds') if timesheet.submitted_at else 'Not submitted'}",
            styles["Normal"],
        ),
        Spacer(1, 0.2 * inch),
    ]

    table_data: list[list[object]] = [
        ["Date", "Family", "Start", "End", "Hours", "Parent Signature"]]
    if entries:
        for entry in entries:
            table_data.append([
                str(entry.work_date),
                entry.family_name,
                entry.start_time.strftime("%H:%M"),
                entry.end_time.strftime("%H:%M"),
                str(entry.total_hours),
                _signature_cell(entry, styles),
            ])
    else:
        table_data.append(["-", "No entries", "-", "-", "0.00",
                          Paragraph('<font color="red">UNSIGNED</font>', styles["BodyText"])])

    table = Table(table_data, colWidths=[
                  0.9 * inch, 1.8 * inch, 0.8 * inch, 0.8 * inch, 0.7 * inch, 2.1 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([table, Spacer(1, 0.2 * inch)])

    summary_data = [
        ["Total Hours", str(total_hours)],
        ["Signed Entries", str(signed_count)],
        ["Unsigned Entries", str(unsigned_count)],
        ["Status", timesheet.status],
    ]
    summary_table = Table(summary_data, colWidths=[2.0 * inch, 2.2 * inch])
    summary_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f3f4f6")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(summary_table)

    document.build(story)
    return buffer.getvalue()
