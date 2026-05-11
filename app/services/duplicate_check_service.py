"""Duplicate detection driven by admin-configured unique flags."""

from app.field_definitions import (
    MODULE_BILL,
    MODULE_CATEGORY,
    MODULE_EMPLOYEE,
    MODULE_ITEM,
    MODULE_VENDOR,
)
from app.extensions import db
from app.models.employee import Employee
from app.models.inventory import Category, ItemMaster, VendorBill
from app.models.vendor import Vendor
from app.services.field_rules_service import get_rules_for_module


def _norm(s: str | None) -> str:
    return (s or "").strip().lower()


def vendor_duplicate_errors(
    form,
    *,
    exclude_vendor_id: int | None = None,
) -> None:
    rules = get_rules_for_module(MODULE_VENDOR)
    vname = form.vendor_name.data
    vcode = form.vendor_code.data

    if rules.get("vendor_name", {}).get("unique") and vname:
        q = Vendor.query.filter(
            Vendor.deleted_at.is_(None),
            db.func.lower(Vendor.vendor_name) == _norm(vname),
        )
        if exclude_vendor_id:
            q = q.filter(Vendor.id != exclude_vendor_id)
        if q.first():
            form.vendor_name.errors.append(
                "A supplier with this name already exists. Please use a distinct name or edit the existing vendor."
            )

    if rules.get("vendor_code", {}).get("unique") and vcode:
        q = Vendor.query.filter(
            Vendor.deleted_at.is_(None),
            Vendor.vendor_code == vcode.strip(),
        )
        if exclude_vendor_id:
            q = q.filter(Vendor.id != exclude_vendor_id)
        if q.first():
            form.vendor_code.errors.append("This vendor code is already in use.")


def bill_duplicate_errors(
    form,
    *,
    exclude_bill_id: int | None = None,
) -> None:
    rules = get_rules_for_module(MODULE_BILL)
    bill_no = form.vendor_bill_no.data
    vid = form.vendor_id.data
    if not rules.get("vendor_bill_no", {}).get("unique") or not bill_no or not vid:
        return
    q = VendorBill.query.filter(
        VendorBill.deleted_at.is_(None),
        VendorBill.vendor_id == vid,
        VendorBill.vendor_bill_no == bill_no.strip(),
    )
    if exclude_bill_id:
        q = q.filter(VendorBill.id != exclude_bill_id)
    if q.first():
        form.vendor_bill_no.errors.append(
            "This vendor bill number already exists for the selected vendor."
        )


def item_duplicate_errors(form, *, exclude_item_id: int | None = None) -> None:
    rules = get_rules_for_module(MODULE_ITEM)
    code = form.item_code.data
    if not rules.get("item_code", {}).get("unique") or not code:
        return
    q = ItemMaster.query.filter(
        ItemMaster.deleted_at.is_(None),
        ItemMaster.item_code == code.strip(),
    )
    if exclude_item_id:
        q = q.filter(ItemMaster.id != exclude_item_id)
    if q.first():
        form.item_code.errors.append("This item code is already in use.")


def employee_duplicate_errors(
    form,
    *,
    exclude_employee_id: int | None = None,
) -> None:
    rules = get_rules_for_module(MODULE_EMPLOYEE)
    code = form.employee_code.data
    if not rules.get("employee_code", {}).get("unique") or not code:
        return
    q = Employee.query.filter(
        Employee.deleted_at.is_(None),
        Employee.employee_code == code.strip(),
    )
    if exclude_employee_id:
        q = q.filter(Employee.id != exclude_employee_id)
    if q.first():
        form.employee_code.errors.append("This employee code is already in use.")


def category_duplicate_errors(form, *, exclude_category_id: int | None = None) -> None:
    rules = get_rules_for_module(MODULE_CATEGORY)
    name = (form.name.data or "").strip()
    if not name or not rules.get("name", {}).get("unique"):
        return
    q = Category.query.filter(db.func.lower(Category.name) == name.lower())
    if exclude_category_id:
        q = q.filter(Category.id != exclude_category_id)
    if q.first():
        form.name.errors.append("A category with this name already exists.")
