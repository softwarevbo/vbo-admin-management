"""Dashboard aggregates."""
from calendar import monthrange
from datetime import date, datetime, timezone

from sqlalchemy import func, extract

from app.constants import BILL_STATUS_PENDING, BILL_STATUS_PAID, BILL_STATUS_UNDER_REVIEW
from app.extensions import db
from app.models.employee import Employee
from app.models.inventory import ItemIssue, ItemMaster, StockLot, VendorBill
from app.models.vendor import Vendor


def get_summary():
    today = date.today()
    start_month = date(today.year, today.month, 1)
    _, last_day = monthrange(today.year, today.month)
    end_month = date(today.year, today.month, last_day)

    total_vendors = Vendor.query.filter(Vendor.deleted_at.is_(None)).count()
    total_bills = VendorBill.query.filter(VendorBill.deleted_at.is_(None)).count()
    pending_bills = VendorBill.query.filter(
        VendorBill.deleted_at.is_(None),
        VendorBill.bill_status.in_(
            [BILL_STATUS_PENDING, BILL_STATUS_UNDER_REVIEW]
        ),
    ).count()
    paid_bills = VendorBill.query.filter(
        VendorBill.deleted_at.is_(None),
        VendorBill.bill_status == BILL_STATUS_PAID,
    ).count()

    total_items = ItemMaster.query.filter(ItemMaster.deleted_at.is_(None)).count()

    low_stock_rows = (
        db.session.query(ItemMaster.id, ItemMaster.item_code, ItemMaster.item_name)
        .outerjoin(
            StockLot,
            (StockLot.item_master_id == ItemMaster.id)
            & (StockLot.deleted_at.is_(None)),
        )
        .filter(ItemMaster.deleted_at.is_(None))
        .group_by(ItemMaster.id)
        .having(
            func.coalesce(func.sum(StockLot.quantity_available), 0)
            < func.coalesce(ItemMaster.minimum_stock_alert, 0)
        )
        .limit(10)
        .all()
    )

    recent_issues = (
        ItemIssue.query.filter(ItemIssue.deleted_at.is_(None))
        .order_by(ItemIssue.created_at.desc())
        .limit(8)
        .all()
    )

    monthly_expense = (
        db.session.query(
            extract("month", VendorBill.vendor_bill_date).label("m"),
            func.sum(VendorBill.total_amount),
        )
        .filter(
            VendorBill.deleted_at.is_(None),
            extract("year", VendorBill.vendor_bill_date) == today.year,
        )
        .group_by("m")
        .order_by("m")
        .all()
    )

    gst_month = (
        db.session.query(func.sum(VendorBill.gst_amount))
        .filter(
            VendorBill.deleted_at.is_(None),
            VendorBill.vendor_bill_date >= start_month,
            VendorBill.vendor_bill_date <= end_month,
        )
        .scalar()
        or 0
    )

    vendor_payments = (
        db.session.query(
            Vendor.vendor_name,
            func.sum(VendorBill.total_amount),
        )
        .join(VendorBill, VendorBill.vendor_id == Vendor.id)
        .filter(
            VendorBill.deleted_at.is_(None),
            VendorBill.bill_status == BILL_STATUS_PAID,
        )
        .group_by(Vendor.id)
        .order_by(func.sum(VendorBill.total_amount).desc())
        .limit(8)
        .all()
    )

    dept_issues = (
        db.session.query(
            Employee.department,
            func.count(ItemIssue.id),
        )
        .join(ItemIssue, ItemIssue.employee_id == Employee.id)
        .filter(ItemIssue.deleted_at.is_(None))
        .group_by(Employee.department)
        .all()
    )

    return {
        "total_vendors": total_vendors,
        "total_bills": total_bills,
        "pending_bills": pending_bills,
        "paid_bills": paid_bills,
        "total_items": total_items,
        "low_stock": low_stock_rows,
        "recent_issues": recent_issues,
        "monthly_expense": [(int(r[0] or 0), float(r[1] or 0)) for r in monthly_expense],
        "gst_month": float(gst_month),
        "vendor_payments": [(r[0], float(r[1] or 0)) for r in vendor_payments],
        "dept_issues": [(r[0] or "N/A", int(r[1])) for r in dept_issues],
        "as_of": datetime.now(timezone.utc),
    }
