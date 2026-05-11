"""Application-wide constants."""

ROLE_SUPER_ADMIN = "super_admin"
ROLE_ADMIN = "admin"
ROLE_ACCOUNTS = "accounts"
ROLE_INVENTORY_MANAGER = "inventory_manager"
ROLE_STORE_KEEPER = "store_keeper"
ROLE_STAFF_VIEWER = "staff_viewer"

ROLE_LABELS = {
    ROLE_SUPER_ADMIN: "Super Admin",
    ROLE_ADMIN: "Admin",
    ROLE_ACCOUNTS: "Accounts Department",
    ROLE_INVENTORY_MANAGER: "Inventory Manager",
    ROLE_STORE_KEEPER: "Store Keeper",
    ROLE_STAFF_VIEWER: "Employee / Staff Viewer",
}

BILL_STATUS_PENDING = "pending"
BILL_STATUS_UNDER_REVIEW = "under_review"
BILL_STATUS_APPROVED = "approved"
BILL_STATUS_REJECTED = "rejected"
BILL_STATUS_PAID = "paid"

PAYMENT_STATUS_UNPAID = "unpaid"
PAYMENT_STATUS_PARTIAL = "partial"
PAYMENT_STATUS_PAID = "paid"

ISSUE_STATUS_ACTIVE = "active"
ISSUE_STATUS_RETURNED = "returned"
ISSUE_STATUS_PARTIAL_RETURN = "partial_return"
ISSUE_STATUS_LOST = "lost"
ISSUE_STATUS_DAMAGED = "damaged"

APPROVAL_PENDING = "pending"
APPROVAL_APPROVED = "approved"
APPROVAL_REJECTED = "rejected"
