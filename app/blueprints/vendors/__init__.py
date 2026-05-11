from datetime import datetime, timezone

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.field_definitions import MODULE_VENDOR
from app.constants import ROLE_ADMIN, ROLE_INVENTORY_MANAGER, ROLE_SUPER_ADMIN
from app.extensions import db
from app.forms.vendor import VendorForm
from app.models.vendor import Vendor
from app.services import audit_service
from app.services.duplicate_check_service import vendor_duplicate_errors
from app.services.field_rules_service import get_field_view, get_rules_for_module
from app.utils.decorators import role_required
from app.utils.dynamic_forms import apply_rules_to_form, validate_submission

bp = Blueprint("vendors", __name__)


@bp.before_request
@login_required
def _auth():
    pass


def _can_manage_vendors():
    return current_user.role and current_user.role.name in (
        ROLE_SUPER_ADMIN,
        ROLE_ADMIN,
        ROLE_INVENTORY_MANAGER,
    )


@bp.route("/")
def list_vendors():
    q = Vendor.query.filter(Vendor.deleted_at.is_(None)).order_by(Vendor.vendor_name)
    search = request.args.get("q", "").strip()
    if search:
        like = f"%{search}%"
        q = q.filter(
            (Vendor.vendor_name.ilike(like))
            | (Vendor.vendor_code.ilike(like))
            | (Vendor.gstin_number.ilike(like))
        )
    active = request.args.get("active")
    if active == "1":
        q = q.filter(Vendor.is_active.is_(True))
    elif active == "0":
        q = q.filter(Vendor.is_active.is_(False))
    vendors = q.limit(500).all()
    return render_template(
        "vendors/list.html",
        vendors=vendors,
        search=search,
        active=active,
        can_manage=_can_manage_vendors(),
    )


@bp.route("/new", methods=["GET", "POST"])
@role_required(ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_INVENTORY_MANAGER)
def new_vendor():
    return _vendor_edit(None)


@bp.route("/<int:vid>/edit", methods=["GET", "POST"])
def edit_vendor(vid):
    if not _can_manage_vendors():
        flash("Permission denied.", "danger")
        return redirect(url_for("vendors.list_vendors"))
    return _vendor_edit(vid)


def _vendor_edit(vid):
    vendor = (
        Vendor.query.filter_by(id=vid, deleted_at=None).first_or_404()
        if vid
        else None
    )
    form = VendorForm(obj=vendor)
    rules = get_rules_for_module(MODULE_VENDOR)
    apply_rules_to_form(form, rules)
    # Apply label overrides on the WTForms fields (for UI only)
    for row in get_field_view(MODULE_VENDOR):
        if row.get("label") and hasattr(form, row["key"]):
            getattr(form, row["key"]).label.text = row["label"]

    if validate_submission(
        form,
        MODULE_VENDOR,
        "vendor_upsert",
        duplicate_checker=lambda: vendor_duplicate_errors(
            form, exclude_vendor_id=vendor.id if vendor else None
        ),
    ):
        if not vendor:
            vendor = Vendor()
            db.session.add(vendor)
        form.populate_obj(vendor)
        vendor.vendor_code = form.vendor_code.data.strip() if form.vendor_code.data else ""
        vendor.vendor_name = form.vendor_name.data.strip() if form.vendor_name.data else ""
        vendor.gstin_number = (
            form.gstin_number.data.strip().upper() if form.gstin_number.data else None
        )
        if form.ifsc_code.data:
            vendor.ifsc_code = form.ifsc_code.data.strip().upper()
        db.session.commit()
        audit_service.log_action(
            "vendor_save", entity_type="vendor", entity_id=vendor.id
        )
        db.session.commit()
        flash("Vendor details saved successfully.", "success")
        return redirect(url_for("vendors.list_vendors"))
    return render_template(
        "vendors/form.html",
        form=form,
        vendor=vendor,
        field_rules=rules,
        module=MODULE_VENDOR,
        field_view=get_field_view(MODULE_VENDOR),
    )


@bp.route("/<int:vid>/delete", methods=["POST"])
@role_required(ROLE_SUPER_ADMIN, ROLE_ADMIN)
def delete_vendor(vid):
    v = Vendor.query.get_or_404(vid)
    v.deleted_at = datetime.now(timezone.utc)
    db.session.commit()
    flash("Vendor archived.", "info")
    return redirect(url_for("vendors.list_vendors"))
