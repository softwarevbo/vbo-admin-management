"""Create and adjust stock lots from bill lines."""
from decimal import Decimal

from app.extensions import db
from app.models.inventory import BillLineItem, StockLot, StockMovement


def create_lots_for_bill_lines(bill, user_id: int | None = None):
    """
    For each line with item_master_id, create one stock lot if none exists.
    quantity_received = line.quantity, quantity_available same.
    """
    for line in bill.lines:
        if not line.item_master_id:
            continue
        if line.stock_lots:
            continue
        qty = Decimal(str(line.quantity))
        unit_cost = Decimal(str(line.unit_price))
        lot = StockLot(
            bill_line_id=line.id,
            item_master_id=line.item_master_id,
            quantity_received=qty,
            quantity_available=qty,
            unit_cost=unit_cost,
            storage_location=None,
        )
        db.session.add(lot)
        db.session.flush()
        db.session.add(
            StockMovement(
                stock_lot_id=lot.id,
                delta_qty=qty,
                reason="receipt",
                reference_type="vendor_bill",
                reference_id=bill.id,
                user_id=user_id,
                note="Stock lot created on bill approval",
            )
        )


def available_on_lot(lot: StockLot) -> Decimal:
    return Decimal(str(lot.quantity_available or 0))
