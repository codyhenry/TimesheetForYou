from decimal import Decimal
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import TimeEntry


def _paragraph(value, styles):
    return Paragraph(escape(str(value or "—")), styles["BodyText"])


def _signature_image(image_field):
    if not image_field:
        return None
    try:
        image_field.open("rb")
        try:
            image_data = BytesIO(image_field.read())
        finally:
            image_field.close()
        if image_data.getbuffer().nbytes:
            image_data.seek(0)
            return Image(image_data, width=1.2 * inch, height=0.4 * inch)
    except Exception:
        return None
    return None


def _signature_cell(entry, styles):
    if entry.signature_status == TimeEntry.SignatureStatus.SIGNED and hasattr(entry, "parent_signature"):
        signature_image = _signature_image(entry.parent_signature.image)
        if signature_image is not None:
            return signature_image
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
            f"Nanny: {escape(timesheet.nanny.get_full_name() or timesheet.nanny.username)}", styles["Normal"]),
        Paragraph(
            f"Week: {timesheet.week_start_date} to {timesheet.week_end_date}", styles["Normal"]),
        Paragraph(
            f"Submitted: {timesheet.submitted_at.isoformat(sep=' ', timespec='seconds') if timesheet.submitted_at else 'Not submitted'}",
            styles["Normal"],
        ),
        Spacer(1, 0.2 * inch),
    ]

    table_data: list[list[object]] = [
        [
            "Date",
            "Family",
            "Start",
            "End",
            "Hours",
            "Requested",
            "Notes",
            "Parent Signature",
        ]
    ]
    if entries:
        for entry in entries:
            table_data.append([
                str(entry.work_date),
                _paragraph(entry.family_name, styles),
                entry.start_time.strftime("%H:%M"),
                entry.end_time.strftime("%H:%M"),
                str(entry.total_hours),
                "Yes" if entry.family_requested_nanny else "No",
                _paragraph(entry.notes, styles),
                _signature_cell(entry, styles),
            ])
    else:
        table_data.append([
            "-",
            "No entries",
            "-",
            "-",
            "0.00",
            "No",
            "—",
            Paragraph('<font color="red">UNSIGNED</font>', styles["BodyText"]),
        ])

    table = Table(
        table_data,
        colWidths=[
            0.72 * inch,
            1.0 * inch,
            0.52 * inch,
            0.52 * inch,
            0.55 * inch,
            0.72 * inch,
            1.45 * inch,
            1.55 * inch,
        ],
        repeatRows=1,
    )
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
    ]))
    story.extend([table, Spacer(1, 0.2 * inch)])

    summary_data = [
        ["Total Hours", str(total_hours)],
        ["Signed Entries", str(signed_count)],
        ["Unsigned Entries", str(unsigned_count)],
        ["Status", timesheet.get_status_display()],
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
