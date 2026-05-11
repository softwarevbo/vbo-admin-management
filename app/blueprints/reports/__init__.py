import pandas as pd
from flask import Blueprint, Response, current_app, render_template, request
from flask_login import login_required
from sqlalchemy import func

from app.constants import (
    ROLE_ACCOUNTS,
    ROLE_ADMIN,
    ROLE_INVENTORY_MANAGER,
    ROLE_STAFF_VIEWER,
    ROLE_STORE_KEEPER,
    ROLE_SUPER_ADMIN,
)
from app.extensions import db
from app.models.inventory import ItemIssue, ItemMaster, StockLot, VendorBill
from app.reports.excel_export import dataframe_to_excel
from app.reports.pdf_bill import build_vendor_bill_pdf
from app.utils.decorators import role_required

bp = Blueprint("reports", __name__)


@bp.before_request
@login_required
def _auth():
    pass


@bp.route("/")
def index():
    return render_template("reports/index.html")


@bp.route("/pdf/bill/<int:bid>")
@role_required(
    ROLE_SUPER_ADMIN,
    ROLE_ADMIN,
    ROLE_ACCOUNTS,
    ROLE_INVENTORY_MANAGER,
    ROLE_STAFF_VIEWER,
    ROLE_STORE_KEEPER,
)
def pdf_bill(bid):
    bill = VendorBill.query.get_or_404(bid)
    pdf_bytes = build_vendor_bill_pdf(
        bill,
        current_app.config["ORG_NAME"],
        current_app.config["ORG_UNIT"],
    )
    fname = f"bill_{bill.bill_register_no or bid}.pdf".replace("/", "-")
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"inline; filename={fname}"},
    )


@bp.route("/excel/bills")
def excel_bills():
    q = VendorBill.query.filter(VendorBill.deleted_at.is_(None)).order_by(
        VendorBill.vendor_bill_date.desc()
    )
    if request.args.get("vendor_id"):
        q = q.filter(VendorBill.vendor_id == int(request.args.get("vendor_id")))
    rows = []
    for b in q.limit(5000):
        rows.append(
            {
                "bill_register_no": b.bill_register_no,
                "vendor_bill_no": b.vendor_bill_no,
                "vendor": b.vendor.vendor_name if b.vendor else "",
                "bill_date": b.vendor_bill_date,
                "status": b.bill_status,
                "payment": b.payment_status,
                "amount": float(b.amount or 0),
                "gst": float(b.gst_amount or 0),
                "total": float(b.total_amount or 0),
            }
        )
    df = pd.DataFrame(rows)
    data = dataframe_to_excel(df, "Bills")
    return Response(
        data,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=bills_export.xlsx"},
    )


@bp.route("/excel/inventory")
def excel_inventory():
    rows = []
    for it in ItemMaster.query.filter(ItemMaster.deleted_at.is_(None)).all():
        avail = (
            db.session.query(func.coalesce(func.sum(StockLot.quantity_available), 0))
            .filter(
                StockLot.item_master_id == it.id,
                StockLot.deleted_at.is_(None),
            )
            .scalar()
        )
        rows.append(
            {
                "item_code": it.item_code,
                "item_name": it.item_name,
                "available": float(avail or 0),
                "min_alert": float(it.minimum_stock_alert or 0),
            }
        )
    df = pd.DataFrame(rows)
    data = dataframe_to_excel(df, "Inventory")
    return Response(
        data,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=inventory_export.xlsx"},
    )


@bp.route("/excel/issues")
def excel_issues():
    rows = []
    for iss in ItemIssue.query.filter(ItemIssue.deleted_at.is_(None)).limit(5000):
        rows.append(
            {
                "issue_code": iss.issue_code,
                "employee": iss.employee.employee_name if iss.employee else "",
                "department": iss.employee.department if iss.employee else "",
                "issue_date": iss.issue_date,
                "status": iss.issue_status,
            }
        )
    df = pd.DataFrame(rows)
    data = dataframe_to_excel(df, "Issues")
    return Response(
        data,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=issues_export.xlsx"},
    )
