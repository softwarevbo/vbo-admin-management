"""Professional PDF for vendor bills (ReportLab)."""
from io import BytesIO
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _money(v) -> str:
    return f"₹ {Decimal(str(v or 0)):,.2f}"


def build_vendor_bill_pdf(bill, org_name: str, org_unit: str) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title="Vendor Bill",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "T",
        parent=styles["Heading1"],
        alignment=TA_CENTER,
        fontSize=14,
        spaceAfter=6,
    )
    sub_style = ParagraphStyle(
        "S",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
    )
    body = [
        Paragraph(org_name, title_style),
        Paragraph(org_unit, sub_style),
        Spacer(1, 0.4 * cm),
        Paragraph("<b>Vendor Bill / Payment Register Copy</b>", styles["Heading2"]),
        Spacer(1, 0.3 * cm),
    ]

    meta = [
        ["Bill Register No.", bill.bill_register_no or "—"],
        ["Vendor Bill No.", bill.vendor_bill_no],
        ["Vendor", bill.vendor.vendor_name if bill.vendor else ""],
        ["Bill Date", str(bill.vendor_bill_date)],
        ["Status", bill.bill_status],
        ["Payment", bill.payment_status],
        ["PO No.", bill.purchase_order_no or "—"],
    ]
    t_meta = Table(meta, colWidths=[5 * cm, 11 * cm])
    t_meta.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    body.append(t_meta)
    body.append(Spacer(1, 0.4 * cm))

    hdr = ["#", "Item / Description", "Qty", "Unit", "Rate", "GST%", "Total"]
    data = [hdr]
    for i, line in enumerate(bill.lines, start=1):
        desc = line.description or (
            line.item_master.item_name if line.item_master else ""
        )
        data.append(
            [
                str(i),
                desc[:60],
                str(line.quantity),
                line.unit or "",
                _money(line.unit_price),
                f"{line.gst_percentage}%",
                _money(line.total_amount),
            ]
        )
    data.append(["", "", "", "", "", "Subtotal", _money(bill.amount)])
    data.append(["", "", "", "", "", "GST", _money(bill.gst_amount)])
    data.append(["", "", "", "", "", "Grand Total", _money(bill.total_amount)])

    table = Table(
        data, colWidths=[1 * cm, 5.5 * cm, 1.2 * cm, 1.2 * cm, 2 * cm, 1.5 * cm, 2.6 * cm]
    )
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
        )
    )
    body.append(table)
    body.append(Spacer(1, 1 * cm))
    body.append(
        Paragraph(
            "<b>Approval &amp; Accounts</b><br/><br/>"
            "Prepared By: ____________________ &nbsp;&nbsp; "
            "Verified By: ____________________<br/><br/>"
            "Authorized Signatory: ____________________",
            styles["Normal"],
        )
    )
    body.append(Spacer(1, 0.5 * cm))

    def _footer(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.drawString(1.5 * cm, 1 * cm, f"Bill ID {bill.id} — Page {canvas.getPageNumber()}")
        canvas.restoreState()

    doc.build(body, onFirstPage=_footer, onLaterPages=_footer)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
