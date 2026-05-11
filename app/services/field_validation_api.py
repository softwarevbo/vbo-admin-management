"""Lightweight duplicate / presence checks for AJAX (calls same rules as forms)."""

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


def check_field_remote(
    module: str,
    field: str,
    value: str,
    *,
    exclude_id: int | None = None,
    exclude_bill_id: int | None = None,
    vendor_id: int | None = None,
) -> tuple[bool, str]:
    """
    Returns (ok, message). Only enforces uniqueness when admin enabled it for that field.
    """
    value = (value or "").strip()
    rules = get_rules_for_module(module).get(field) or {}

    if not rules.get("unique"):
        return True, ""

    if module == MODULE_VENDOR and field == "vendor_name":
        q = Vendor.query.filter(
            Vendor.deleted_at.is_(None),
            db.func.lower(Vendor.vendor_name) == value.lower(),
        )
        if exclude_id:
            q = q.filter(Vendor.id != exclude_id)
        if value and q.first():
            return False, "This vendor name is already registered."
        return True, ""

    if module == MODULE_VENDOR and field == "vendor_code":
        q = Vendor.query.filter(
            Vendor.deleted_at.is_(None),
            Vendor.vendor_code == value,
        )
        if exclude_id:
            q = q.filter(Vendor.id != exclude_id)
        if value and q.first():
            return False, "This vendor code is already in use."
        return True, ""

    if module == MODULE_EMPLOYEE and field == "employee_code":
        q = Employee.query.filter(
            Employee.deleted_at.is_(None),
            Employee.employee_code == value,
        )
        if exclude_id:
            q = q.filter(Employee.id != exclude_id)
        if value and q.first():
            return False, "This employee code is already in use."
        return True, ""

    if module == MODULE_ITEM and field == "item_code":
        q = ItemMaster.query.filter(
            ItemMaster.deleted_at.is_(None),
            ItemMaster.item_code == value,
        )
        if exclude_id:
            q = q.filter(ItemMaster.id != exclude_id)
        if value and q.first():
            return False, "This item code is already in use."
        return True, ""

    if module == MODULE_CATEGORY and field == "name":
        q = Category.query.filter(db.func.lower(Category.name) == value.lower())
        if exclude_id:
            q = q.filter(Category.id != exclude_id)
        if value and q.first():
            return False, "This category name already exists."
        return True, ""

    if module == MODULE_BILL and field == "vendor_bill_no":
        if not vendor_id or not value:
            return True, ""
        q = VendorBill.query.filter(
            VendorBill.deleted_at.is_(None),
            VendorBill.vendor_id == vendor_id,
            VendorBill.vendor_bill_no == value,
        )
        eid = exclude_bill_id or exclude_id
        if eid:
            q = q.filter(VendorBill.id != eid)
        if q.first():
            return False, "This bill number already exists for the selected vendor."
        return True, ""

    return True, ""
