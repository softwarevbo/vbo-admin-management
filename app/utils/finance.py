"""GST and line amount calculations."""
from decimal import Decimal


def quantize_money(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.01"))


def compute_line_amounts(quantity, unit_price, discount, gst_percent):
    """
    discount: flat amount on line (before GST).
    Returns (line_subtotal, gst_amount, total_amount) as Decimal.
    """
    qty = Decimal(str(quantity))
    price = Decimal(str(unit_price))
    disc = Decimal(str(discount or 0))
    taxable = qty * price - disc
    if taxable < 0:
        taxable = Decimal("0")
    gst_pct = Decimal(str(gst_percent or 0))
    gst = (taxable * gst_pct / Decimal("100")).quantize(Decimal("0.01"))
    total = (taxable + gst).quantize(Decimal("0.01"))
    return taxable.quantize(Decimal("0.01")), gst, total


def sum_bill_from_lines(lines):
    """Aggregate header totals from iterable of line objects with monetary attrs."""
    sub = Decimal("0")
    gst = Decimal("0")
    tot = Decimal("0")
    for line in lines:
        sub += Decimal(str(line.line_subtotal or 0))
        gst += Decimal(str(line.gst_amount or 0))
        tot += Decimal(str(line.total_amount or 0))
    return (
        sub.quantize(Decimal("0.01")),
        gst.quantize(Decimal("0.01")),
        tot.quantize(Decimal("0.01")),
    )
