from datetime import date, datetime, timezone

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from app.constants import (
    BILL_STATUS_PENDING,
    BILL_STATUS_REJECTED,
    BILL_STATUS_UNDER_REVIEW,
    ROLE_ACCOUNTS,
    ROLE_ADMIN,
    ROLE_INVENTORY_MANAGER,
    ROLE_STAFF_VIEWER,
    ROLE_SUPER_ADMIN,
)
from app.field_definitions import MODULE_BILL, MODULE_BILL_LINE
from app.extensions import db
from app.forms.bill import BillLineForm, BillWorkflowForm, VendorBillForm
from app.models.inventory import BillLineItem, ItemMaster, VendorBill
from app.models.vendor import Vendor
from app.services import audit_service, bill_service
from app.services.duplicate_check_service import bill_duplicate_errors
from app.services.field_rules_service import get_field_view, get_rules_for_module
from app.utils.decorators import role_required
from app.utils.dynamic_forms import apply_rules_to_form, validate_submission
from app.utils.security import allowed_file, save_upload

bp = Blueprint("bills", __name__)


@bp.before_request
@login_required
def _auth():
    pass


def _vendor_choices():
    return [
        (v.id, f"{v.vendor_code} — {v.vendor_name}")
        for v in Vendor.query.filter(
            Vendor.deleted_at.is_(None), Vendor.is_active.is_(True)
        )
        .order_by(Vendor.vendor_name)
        .limit(2000)
        .all()
    ]


def _item_choices():
    return [
        (i.id, f"{i.item_code} — {i.item_name}")
        for i in ItemMaster.query.filter(
            ItemMaster.deleted_at.is_(None), ItemMaster.is_active.is_(True)
        )
        .order_by(ItemMaster.item_name)
        .limit(5000)
        .all()
    ]


@bp.route("/")
def list_bills():
    q = VendorBill.query.filter(VendorBill.deleted_at.is_(None)).order_by(
        VendorBill.created_at.desc()
    )
    if request.args.get("vendor_id"):
        q = q.filter(VendorBill.vendor_id == int(request.args.get("vendor_id")))
    if request.args.get("status"):
        q = q.filter(VendorBill.bill_status == request.args.get("status"))
    if request.args.get("from_date"):
        q = q.filter(VendorBill.vendor_bill_date >= request.args.get("from_date"))
    if request.args.get("to_date"):
        q = q.filter(VendorBill.vendor_bill_date <= request.args.get("to_date"))
    bills = q.limit(500).all()
    vendors = Vendor.query.filter(Vendor.deleted_at.is_(None)).order_by(Vendor.vendor_name).all()
    return render_template(
        "bills/list.html",
        bills=bills,
        vendors=vendors,
        args=request.args,
    )


@bp.route("/new", methods=["GET", "POST"])
def new_bill():
    if current_user.role.name == ROLE_STAFF_VIEWER:
        flash("Read-only role.", "danger")
        return redirect(url_for("bills.list_bills"))
    form = VendorBillForm()
    form.vendor_id.choices = _vendor_choices()
    bill_rules = get_rules_for_module(MODULE_BILL)
    apply_rules_to_form(form, bill_rules)
    for row in get_field_view(MODULE_BILL):
        if row.get("label") and hasattr(form, row["key"]):
            getattr(form, row["key"]).label.text = row["label"]
    if not form.vendor_id.choices:
        flash("Create at least one vendor before adding bills.", "warning")
        return redirect(url_for("vendors.new_vendor"))
    if validate_submission(
        form,
        MODULE_BILL,
        "bill_create",
        duplicate_checker=lambda: bill_duplicate_errors(form, exclude_bill_id=None),
    ):
        bill = VendorBill(
            vendor_id=form.vendor_id.data,
            vendor_bill_no=(form.vendor_bill_no.data or "").strip(),
            vendor_bill_date=form.vendor_bill_date.data,
            bill_received_date=form.bill_received_date.data,
            division_section=form.division_section.data,
            indenter_end_user=form.indenter_end_user.data,
            purchase_order_no=form.purchase_order_no.data,
            remarks=form.remarks.data,
            bill_status=BILL_STATUS_PENDING,
            created_by=current_user.id,
        )
        db.session.add(bill)
        db.session.flush()
        if form.invoice_file.data:
            f = form.invoice_file.data
            if allowed_file(f.filename, {"pdf", "png", "jpg", "jpeg"}):
                rel = save_upload(
                    f,
                    current_app.config["UPLOAD_FOLDER"],
                    prefix=f"bill_{bill.id}_",
                )
                bill.invoice_file_upload = rel
        db.session.commit()
        audit_service.log_action("bill_create", entity_type="vendor_bill", entity_id=bill.id)
        db.session.commit()
        flash("Bill created successfully. Add line items below.", "success")
        return redirect(url_for("bills.bill_detail", bid=bill.id))
    return render_template(
        "bills/form.html",
        form=form,
        bill=None,
        field_rules=bill_rules,
        module=MODULE_BILL,
        field_view=get_field_view(MODULE_BILL),
    )


@bp.route("/<int:bid>", methods=["GET", "POST"])
def bill_detail(bid):
    bill = VendorBill.query.filter_by(id=bid, deleted_at=None).first_or_404()
    wf = BillWorkflowForm()
    line_form = BillLineForm()
    line_form.item_master_id.choices = [(0, "— Optional —")] + _item_choices()
    line_rules = get_rules_for_module(MODULE_BILL_LINE)
    apply_rules_to_form(line_form, line_rules)
    for row in get_field_view(MODULE_BILL_LINE):
        if row.get("label") and hasattr(line_form, row["key"]):
            getattr(line_form, row["key"]).label.text = row["label"]

    if request.method == "POST":
        if current_user.role.name == ROLE_STAFF_VIEWER:
            flash("Read-only.", "danger")
            return redirect(url_for("bills.bill_detail", bid=bid))

        if "add_line" in request.form:
            line_form = BillLineForm()
            line_form.item_master_id.choices = [(0, "— Optional —")] + _item_choices()
            apply_rules_to_form(line_form, line_rules)
            if validate_submission(
                line_form, MODULE_BILL_LINE, "bill_line_add", duplicate_checker=None
            ):
                data = {
                    "item_master_id": line_form.item_master_id.data or None,
                    "description": line_form.description.data,
                    "quantity": line_form.quantity.data,
                    "unit": line_form.unit.data,
                    "unit_price": line_form.unit_price.data,
                    "discount": line_form.discount.data or 0,
                    "gst_percentage": line_form.gst_percentage.data or 18,
                }
                if data["item_master_id"] == 0:
                    data["item_master_id"] = None
                try:
                    bill_service.upsert_line(bill, None, data)
                    db.session.commit()
                    flash("Line item added successfully.", "success")
                    return redirect(url_for("bills.bill_detail", bid=bid))
                except Exception as exc:
                    db.session.rollback()
                    flash(str(exc), "danger")
        elif wf.validate_on_submit():
            try:
                if wf.submit_review.data:
                    bill_service.submit_for_review(bill)
                elif wf.approve.data and current_user.role.name in (
                    ROLE_SUPER_ADMIN,
                    ROLE_ADMIN,
                    ROLE_INVENTORY_MANAGER,
                ):
                    bill_service.approve_level(bill, wf.comments.data)
                elif wf.reject.data and current_user.role.name in (
                    ROLE_SUPER_ADMIN,
                    ROLE_ADMIN,
                    ROLE_INVENTORY_MANAGER,
                ):
                    bill_service.reject_bill(bill, wf.comments.data)
                elif wf.mark_paid.data and current_user.role.name in (
                    ROLE_SUPER_ADMIN,
                    ROLE_ADMIN,
                    ROLE_ACCOUNTS,
                ):
                    bill_service.mark_paid(bill, wf.payment_date.data or date.today())
                db.session.commit()
                flash("Bill updated.", "success")
            except Exception as exc:
                db.session.rollback()
                flash(str(exc), "danger")
            return redirect(url_for("bills.bill_detail", bid=bid))

    return render_template(
        "bills/detail.html",
        bill=bill,
        wf=wf,
        line_form=line_form,
        field_rules=line_rules,
        bill_line_module=MODULE_BILL_LINE,
        field_view=get_field_view(MODULE_BILL_LINE),
    )


@bp.route("/<int:bid>/line/<int:lid>/delete", methods=["POST"])
def delete_line(bid, lid):
    bill = VendorBill.query.filter_by(id=bid, deleted_at=None).first_or_404()
    if bill.bill_status not in (
        BILL_STATUS_PENDING,
        BILL_STATUS_UNDER_REVIEW,
        BILL_STATUS_REJECTED,
    ):
        flash("Cannot edit lines in current status.", "danger")
        return redirect(url_for("bills.bill_detail", bid=bid))
    line = BillLineItem.query.get_or_404(lid)
    if line.vendor_bill_id != bill.id:
        flash("Invalid line.", "danger")
        return redirect(url_for("bills.bill_detail", bid=bid))
    db.session.delete(line)
    bill_service.recalculate_bill_totals(bill)
    db.session.commit()
    flash("Line removed.", "info")
    return redirect(url_for("bills.bill_detail", bid=bid))


@bp.route("/<int:bid>/delete", methods=["POST"])
@role_required(ROLE_SUPER_ADMIN, ROLE_ADMIN)
def delete_bill(bid):
    bill = VendorBill.query.get_or_404(bid)
    bill.deleted_at = datetime.now(timezone.utc)
    db.session.commit()
    flash("Bill archived.", "info")
    return redirect(url_for("bills.list_bills"))
