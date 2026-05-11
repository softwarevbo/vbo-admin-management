"""Vendor bill workflow and totals."""
from datetime import date

from flask_login import current_user

from app.constants import (
    BILL_STATUS_APPROVED,
    BILL_STATUS_PAID,
    BILL_STATUS_PENDING,
    BILL_STATUS_REJECTED,
    BILL_STATUS_UNDER_REVIEW,
)
from app.extensions import db
from app.models.inventory import BillApprovalLog, BillLineItem, VendorBill
from app.services import audit_service, numbering_service, stock_lot_service
from app.utils.finance import compute_line_amounts, sum_bill_from_lines


def recalculate_bill_totals(bill: VendorBill) -> None:
    sub, gst, tot = sum_bill_from_lines(bill.lines)
    bill.amount = sub
    bill.gst_amount = gst
    bill.total_amount = tot


def upsert_line(
    bill: VendorBill,
    line_id: int | None,
    data: dict,
) -> BillLineItem:
    if line_id:
        line = BillLineItem.query.get_or_404(line_id)
        if line.vendor_bill_id != bill.id:
            raise ValueError("Invalid line")
    else:
        line = BillLineItem(vendor_bill_id=bill.id)
        max_no = max((l.line_no for l in bill.lines), default=0)
        line.line_no = max_no + 1
        db.session.add(line)
    qty = data["quantity"]
    price = data["unit_price"]
    if qty is None or price is None:
        raise ValueError("Quantity and unit price are required for each line item.")
    disc = data.get("discount") or 0
    gst_pct = data.get("gst_percentage") or 18
    sub, gst, total = compute_line_amounts(qty, price, disc, gst_pct)
    line.item_master_id = data.get("item_master_id")
    line.description = data.get("description")
    line.quantity = qty
    line.unit = data.get("unit") or "Nos"
    line.gst_percentage = gst_pct
    line.unit_price = price
    line.discount = disc
    line.line_subtotal = sub
    line.gst_amount = gst
    line.total_amount = total
    db.session.flush()
    recalculate_bill_totals(bill)
    return line


def submit_for_review(bill: VendorBill):
    bill.bill_status = BILL_STATUS_UNDER_REVIEW
    db.session.flush()
    audit_service.log_action(
        "bill_submit_review",
        entity_type="vendor_bill",
        entity_id=bill.id,
    )


def approve_level(bill: VendorBill, comments: str | None = None):
    """Multi-level: inventory_manager then admin/super_admin."""
    if bill.bill_status == BILL_STATUS_APPROVED:
        return
    if bill.bill_status == BILL_STATUS_PAID:
        return
    required = bill.approval_level_required or 2
    bill.current_approval_level = (bill.current_approval_level or 0) + 1
    log = BillApprovalLog(
        vendor_bill_id=bill.id,
        level=bill.current_approval_level,
        action="approved",
        actor_user_id=current_user.id,
        comments=comments,
    )
    db.session.add(log)
    if bill.current_approval_level >= required:
        bill.bill_status = BILL_STATUS_APPROVED
        bill.approved_by = current_user.id
        if not bill.bill_register_no:
            bill.bill_register_no = numbering_service.next_bill_register_no()
        bill.processed_date = bill.processed_date or date.today()
        stock_lot_service.create_lots_for_bill_lines(bill, user_id=current_user.id)
    else:
        bill.bill_status = BILL_STATUS_UNDER_REVIEW
    db.session.flush()
    audit_service.log_action(
        "bill_approve",
        entity_type="vendor_bill",
        entity_id=bill.id,
        details={"level": bill.current_approval_level},
    )


def reject_bill(bill: VendorBill, comments: str | None = None):
    bill.bill_status = BILL_STATUS_REJECTED
    log = BillApprovalLog(
        vendor_bill_id=bill.id,
        level=bill.current_approval_level or 1,
        action="rejected",
        actor_user_id=current_user.id,
        comments=comments,
    )
    db.session.add(log)
    db.session.flush()
    audit_service.log_action(
        "bill_reject",
        entity_type="vendor_bill",
        entity_id=bill.id,
    )


def mark_paid(bill: VendorBill, payment_date):
    if bill.bill_status == BILL_STATUS_PAID:
        return
    if bill.bill_status != BILL_STATUS_APPROVED:
        raise ValueError("Only approved bills can be marked as paid.")
    bill.payment_status = "paid"
    bill.payment_date = payment_date
    bill.bill_status = BILL_STATUS_PAID
    db.session.flush()
    audit_service.log_action(
        "bill_mark_paid",
        entity_type="vendor_bill",
        entity_id=bill.id,
    )


def reset_to_pending(bill: VendorBill):
    """Allow editing after rejection."""
    bill.bill_status = BILL_STATUS_PENDING
    bill.current_approval_level = 0
    db.session.flush()
