"""Item issue / return against stock lots."""
from datetime import date
from decimal import Decimal

from flask_login import current_user

from app.constants import (
    ISSUE_STATUS_ACTIVE,
    ISSUE_STATUS_DAMAGED,
    ISSUE_STATUS_LOST,
    ISSUE_STATUS_PARTIAL_RETURN,
    ISSUE_STATUS_RETURNED,
)
from app.extensions import db
from app.models.inventory import IssueLine, ItemIssue, StockLot, StockMovement
from app.services import audit_service, numbering_service
from app.services.stock_lot_service import available_on_lot


def create_issue(employee_id: int, issue_date, lines: list[dict], remarks=None):
    """
    lines: [{stock_lot_id, quantity, item_condition optional}, ...]
    """
    issue = ItemIssue(
        issue_code=numbering_service.next_issue_code(),
        employee_id=employee_id,
        issued_by=current_user.id,
        issue_date=issue_date,
        issue_status=ISSUE_STATUS_ACTIVE,
        approval_status="approved",
        remarks=remarks,
    )
    db.session.add(issue)
    db.session.flush()
    for row in lines:
        lot = StockLot.query.get_or_404(row["stock_lot_id"])
        qty = Decimal(str(row["quantity"]))
        avail = available_on_lot(lot)
        if qty <= 0 or qty > avail:
            raise ValueError(
                f"Invalid quantity for lot {lot.id}: requested {qty}, available {avail}"
            )
        lot.quantity_available = avail - qty
        il = IssueLine(
            item_issue_id=issue.id,
            stock_lot_id=lot.id,
            issued_quantity=qty,
            returned_quantity=Decimal("0"),
            item_condition=row.get("item_condition"),
        )
        db.session.add(il)
        db.session.add(
            StockMovement(
                stock_lot_id=lot.id,
                delta_qty=-qty,
                reason="issue",
                reference_type="item_issue",
                reference_id=issue.id,
                user_id=current_user.id,
            )
        )
    db.session.flush()
    audit_service.log_action(
        "issue_create",
        entity_type="item_issue",
        entity_id=issue.id,
    )
    return issue


def return_lines(issue: ItemIssue, line_returns: list[dict]):
    """
    line_returns: [{issue_line_id, return_qty, condition}, ...]
    """
    for rr in line_returns:
        line = IssueLine.query.get_or_404(rr["issue_line_id"])
        if line.item_issue_id != issue.id:
            raise ValueError("Line mismatch")
        ret = Decimal(str(rr["return_qty"]))
        issued = Decimal(str(line.issued_quantity))
        already = Decimal(str(line.returned_quantity or 0))
        if ret <= 0 or ret > issued - already:
            raise ValueError("Invalid return quantity")
        line.returned_quantity = already + ret
        cond = rr.get("item_condition") or "good"
        line.item_condition = cond
        lot = line.stock_lot
        if cond != "lost":
            lot.quantity_available = available_on_lot(lot) + ret
            db.session.add(
                StockMovement(
                    stock_lot_id=lot.id,
                    delta_qty=ret,
                    reason="return",
                    reference_type="item_issue",
                    reference_id=issue.id,
                    user_id=current_user.id,
                )
            )
        else:
            db.session.add(
                StockMovement(
                    stock_lot_id=lot.id,
                    delta_qty=0,
                    reason="lost_no_restoral",
                    reference_type="item_issue",
                    reference_id=issue.id,
                    user_id=current_user.id,
                    note=f"Declared lost; issued qty {ret} not restocked",
                )
            )
    db.session.flush()
    all_returned = all(
        Decimal(str(l.returned_quantity or 0)) >= Decimal(str(l.issued_quantity))
        for l in issue.lines
    )
    conds = {rr.get("item_condition") for rr in line_returns}
    if "lost" in conds:
        issue.issue_status = ISSUE_STATUS_LOST
    elif "damaged" in conds:
        issue.issue_status = ISSUE_STATUS_DAMAGED
    elif all_returned:
        issue.issue_status = ISSUE_STATUS_RETURNED
        issue.actual_return_date = issue.actual_return_date or date.today()
    else:
        issue.issue_status = ISSUE_STATUS_PARTIAL_RETURN
    db.session.flush()
    audit_service.log_action(
        "issue_return",
        entity_type="item_issue",
        entity_id=issue.id,
    )
