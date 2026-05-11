"""Registry of form fields per module for admin UI and dynamic validation.

Keys must match WTForms attribute names on the corresponding form class.
"""
from typing import TypedDict


class FieldMeta(TypedDict):
    key: str
    label: str


MODULE_VENDOR = "vendor"
MODULE_BILL = "bill"
MODULE_BILL_LINE = "bill_line"
MODULE_ITEM = "item"
MODULE_EMPLOYEE = "employee"
MODULE_ISSUE = "issue"
MODULE_CATEGORY = "category"

ALL_MODULES = [
    MODULE_VENDOR,
    MODULE_BILL,
    MODULE_BILL_LINE,
    MODULE_ITEM,
    MODULE_CATEGORY,
    MODULE_EMPLOYEE,
    MODULE_ISSUE,
]

MODULE_LABELS = {
    MODULE_VENDOR: "Vendor master",
    MODULE_BILL: "Bill register",
    MODULE_BILL_LINE: "Bill line item",
    MODULE_ITEM: "Item management",
    MODULE_CATEGORY: "Item category",
    MODULE_EMPLOYEE: "Employee management",
    MODULE_ISSUE: "Inventory distribution / issue",
}

FIELD_REGISTRY: dict[str, list[FieldMeta]] = {
    MODULE_VENDOR: [
        {"key": "vendor_code", "label": "Vendor code"},
        {"key": "vendor_name", "label": "Vendor name"},
        {"key": "vendor_company_name", "label": "Company name"},
        {"key": "contact_person", "label": "Contact person"},
        {"key": "mobile_number", "label": "Mobile"},
        {"key": "email", "label": "Email"},
        {"key": "gstin_number", "label": "GSTIN"},
        {"key": "pan_number", "label": "PAN"},
        {"key": "address", "label": "Address"},
        {"key": "city", "label": "City"},
        {"key": "state", "label": "State"},
        {"key": "pincode", "label": "PIN"},
        {"key": "country", "label": "Country"},
        {"key": "bank_name", "label": "Bank name"},
        {"key": "branch_name", "label": "Branch"},
        {"key": "account_holder_name", "label": "Account holder"},
        {"key": "account_number", "label": "Account number"},
        {"key": "ifsc_code", "label": "IFSC"},
        {"key": "swift_code", "label": "SWIFT"},
        {"key": "account_type", "label": "Account type"},
        {"key": "upi_id", "label": "UPI ID"},
    ],
    MODULE_BILL: [
        {"key": "vendor_id", "label": "Vendor"},
        {"key": "vendor_bill_no", "label": "Vendor bill number"},
        {"key": "vendor_bill_date", "label": "Vendor bill date"},
        {"key": "bill_received_date", "label": "Bill received date"},
        {"key": "division_section", "label": "Division / section"},
        {"key": "indenter_end_user", "label": "Indenter / end user"},
        {"key": "purchase_order_no", "label": "PO number"},
        {"key": "remarks", "label": "Remarks"},
        {"key": "invoice_file", "label": "Invoice upload"},
    ],
    MODULE_BILL_LINE: [
        {"key": "item_master_id", "label": "Item master"},
        {"key": "description", "label": "Description"},
        {"key": "quantity", "label": "Quantity"},
        {"key": "unit", "label": "Unit"},
        {"key": "unit_price", "label": "Unit price"},
        {"key": "discount", "label": "Discount"},
        {"key": "gst_percentage", "label": "GST %"},
    ],
    MODULE_ITEM: [
        {"key": "item_code", "label": "Item code"},
        {"key": "item_name", "label": "Item name"},
        {"key": "category_id", "label": "Category"},
        {"key": "description", "label": "Description"},
        {"key": "default_unit", "label": "Unit"},
        {"key": "default_gst_percentage", "label": "Default GST %"},
        {"key": "minimum_stock_alert", "label": "Minimum stock alert"},
    ],
    MODULE_EMPLOYEE: [
        {"key": "employee_code", "label": "Employee code"},
        {"key": "employee_name", "label": "Name"},
        {"key": "email", "label": "Email"},
        {"key": "mobile_number", "label": "Mobile"},
        {"key": "designation", "label": "Designation"},
        {"key": "department_id", "label": "Department (list)"},
        {"key": "department", "label": "Department (text)"},
        {"key": "division_section", "label": "Division / section"},
        {"key": "office_location", "label": "Office location"},
        {"key": "joining_date", "label": "Joining date"},
        {"key": "employment_status", "label": "Employment status"},
        {"key": "address", "label": "Address"},
        {"key": "emergency_contact", "label": "Emergency contact"},
    ],
    MODULE_ISSUE: [
        {"key": "employee_id", "label": "Employee"},
        {"key": "issue_date", "label": "Issue date"},
        {"key": "remarks", "label": "Remarks"},
    ],
    MODULE_CATEGORY: [
        {"key": "name", "label": "Category name"},
        {"key": "description", "label": "Description"},
    ],
}

# Suggested uniqueness (admin can toggle) — used as default when seeding rows
DEFAULT_UNIQUE_FIELDS = {
    MODULE_VENDOR: ("vendor_code", "vendor_name"),
    MODULE_BILL: ("vendor_bill_no",),
    MODULE_ITEM: ("item_code",),
    MODULE_EMPLOYEE: ("employee_code",),
    MODULE_CATEGORY: ("name",),
    MODULE_ISSUE: (),
    MODULE_BILL_LINE: (),
}
