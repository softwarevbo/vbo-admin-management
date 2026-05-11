"""Service functions for the About Me / User Guidance dashboard."""
from datetime import datetime, timezone

from flask_login import current_user
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
from app.models.audit import AuditLog
from app.models.guidance import Announcement, RoleGuidance
from app.models.inventory import ItemMaster, StockLot, VendorBill
from app.models.inventory import ItemIssue
from app.models.vendor import Vendor


def _role_name() -> str | None:
    if not current_user.is_authenticated or not current_user.role:
        return None
    return current_user.role.name


def get_role_profile() -> dict:
    """Return high-level description and allowed modules by role."""
    r = _role_name()
    if not r:
        return {}
    guidance = RoleGuidance.query.filter_by(role_name=r).first()

    # Default module descriptions per role (can be refined from modules_json later)
    base_modules = []
    if r in (ROLE_SUPER_ADMIN, ROLE_ADMIN):
        base_modules = [
            {
                "name": "Vendors",
                "description": "Maintain vendor master and banking details.",
                "endpoint": "vendors.list_vendors",
                "actions": ["create", "edit", "archive", "search", "export"],
            },
            {
                "name": "Vendor bills",
                "description": "Register, review, approve and track payments.",
                "endpoint": "bills.list_bills",
                "actions": ["create", "edit", "approve", "mark paid", "export"],
            },
            {
                "name": "Inventory & items",
                "description": "Manage item master, categories, and stock lots.",
                "endpoint": "inventory.list_items",
                "actions": ["create", "edit", "monitor stock"],
            },
            {
                "name": "Issues",
                "description": "Issue items to staff and record returns.",
                "endpoint": "issues.list_issues",
                "actions": ["issue", "record return"],
            },
            {
                "name": "Reports",
                "description": "Download Excel/PDF reports and summaries.",
                "endpoint": "reports.index",
                "actions": ["view reports", "export Excel/PDF"],
            },
        ]
    elif r == ROLE_ACCOUNTS:
        base_modules = [
            {
                "name": "Vendor bills",
                "description": "Enter, review, and mark bills as paid.",
                "endpoint": "bills.list_bills",
                "actions": ["create", "edit", "mark paid", "export"],
            },
            {
                "name": "Reports",
                "description": "GST, payment and expense reports.",
                "endpoint": "reports.index",
                "actions": ["GST summary", "expense reports", "export"],
            },
        ]
    elif r == ROLE_INVENTORY_MANAGER:
        base_modules = [
            {
                "name": "Items & categories",
                "description": "Maintain item master and inventory categories.",
                "endpoint": "inventory.list_items",
                "actions": ["create", "edit", "monitor stock"],
            },
            {
                "name": "Vendor bills (stock)",
                "description": "Review and approve stock-related bills.",
                "endpoint": "bills.list_bills",
                "actions": ["review", "approve"],
            },
            {
                "name": "Issues",
                "description": "Track issues and returns to employees.",
                "endpoint": "issues.list_issues",
                "actions": ["issue", "review returns"],
            },
        ]
    elif r == ROLE_STORE_KEEPER:
        base_modules = [
            {
                "name": "Stock lots",
                "description": "View lots created from approved bills.",
                "endpoint": "inventory.stock_lots",
                "actions": ["monitor availability"],
            },
            {
                "name": "Issues",
                "description": "Issue or receive items from employees.",
                "endpoint": "issues.list_issues",
                "actions": ["issue", "return"],
            },
        ]
    elif r == ROLE_STAFF_VIEWER:
        base_modules = [
            {
                "name": "Dashboard",
                "description": "View high-level status and summaries.",
                "endpoint": "main.dashboard",
                "actions": ["view only"],
            },
            {
                "name": "Reports",
                "description": "Read-only access to permitted reports.",
                "endpoint": "reports.index",
                "actions": ["view only"],
            },
        ]

    modules = guidance.modules_json or base_modules
    return {
        "role_name": r,
        "title": guidance.title if guidance else None,
        "responsibilities_md": guidance.responsibilities_md if guidance else "",
        "workflow_md": guidance.workflow_md if guidance else "",
        "modules": modules,
    }


def get_user_summary() -> dict:
    """Cards/metrics for the About Me page."""
    if not current_user.is_authenticated:
        return {}
    user_id = current_user.id

    # Last 10 logins / actions
    recent_activity = (
        AuditLog.query.filter(AuditLog.user_id == user_id)
        .order_by(AuditLog.created_at.desc())
        .limit(10)
        .all()
    )

    # Pending approvals, unprocessed bills, low stock
    pending_bills = (
        VendorBill.query.filter(
            VendorBill.deleted_at.is_(None),
            VendorBill.bill_status.in_(["pending", "under_review"]),
        )
        .count()
    )
    low_stock_rows = (
        db.session.query(ItemMaster.id)
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
        .count()
    )

    open_issues = (
        ItemIssue.query.filter(
            ItemIssue.deleted_at.is_(None),
            ItemIssue.issue_status.in_(["active", "partial_return"]),
        )
        .count()
    )

    return {
        "pending_bills": pending_bills,
        "low_stock_count": low_stock_rows,
        "open_issues": open_issues,
        "recent_activity": recent_activity,
    }


def get_announcements_for_user():
    """Return active announcements for current user's role."""
    r = _role_name()
    q = Announcement.query.filter_by(is_active=True)
    if r:
        q = q.filter(
            (Announcement.audience_role.is_(None))
            | (Announcement.audience_role == r)
        )
    return q.order_by(Announcement.created_at.desc()).all()

