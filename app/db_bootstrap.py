"""Create tables and default rows (idempotent). Used by CLI and app factory."""
import os

from app.constants import (
    ROLE_ACCOUNTS,
    ROLE_ADMIN,
    ROLE_INVENTORY_MANAGER,
    ROLE_STAFF_VIEWER,
    ROLE_STORE_KEEPER,
    ROLE_SUPER_ADMIN,
)
from app.extensions import db
from app.models.employee import Department
from app.models.guidance import Announcement, RoleGuidance
from app.models.inventory import Category
from app.models.user import Role, User
from app.services.field_rules_service import seed_default_rules


def run_seed():
    """Ensure roles, admin user, and minimal reference data exist."""
    roles_data = [
        (ROLE_SUPER_ADMIN, "Full system access"),
        (ROLE_ADMIN, "Administrative access"),
        (ROLE_ACCOUNTS, "Bills, payments, GST"),
        (ROLE_INVENTORY_MANAGER, "Items, stock, approvals"),
        (ROLE_STORE_KEEPER, "Issues and returns"),
        (ROLE_STAFF_VIEWER, "Read-only dashboards"),
    ]
    for name, desc in roles_data:
        if not Role.query.filter_by(name=name).first():
            db.session.add(Role(name=name, description=desc))
    db.session.commit()

    admin_role = Role.query.filter_by(name=ROLE_SUPER_ADMIN).first()
    if admin_role and not User.query.filter_by(username="admin").first():
        u = User(
            username="admin",
            email="admin@vbo.iia.res.in",
            full_name="System Administrator",
            role_id=admin_role.id,
            is_active=True,
        )
        u.set_password("admin123")
        db.session.add(u)
        db.session.commit()

    if not Category.query.filter_by(name="General").first():
        db.session.add(Category(name="General", description="Default category"))
    if not Department.query.filter_by(name="Observatory").first():
        db.session.add(Department(name="Observatory", division="Operations"))
    db.session.commit()
    _seed_guidance()
    seed_default_rules()


def _seed_guidance():
    """Insert basic role guidance rows if missing."""
    defaults = {
        "super_admin": {
            "title": "Super Admin — full system access",
            "responsibilities_md": (
                "- Configure users, roles, and permissions.\n"
                "- Maintain master data (vendors, items, employees, departments).\n"
                "- Oversee bill approvals, payments, and inventory flows.\n"
                "- Monitor audit logs, validation logs, and system health.\n"
            ),
            "workflow_md": (
                "1. Create / review master data (vendors, categories, employees).\n"
                "2. Monitor vendor bills and approval queues.\n"
                "3. Ensure stock lots and issues are correctly processed.\n"
                "4. Periodically review reports, exports, and audit records.\n"
            ),
        },
        "admin": {
            "title": "Admin — configuration & oversight",
            "responsibilities_md": (
                "- Manage application users and roles.\n"
                "- Configure mandatory fields and duplicate rules.\n"
                "- Support departments in using the system correctly.\n"
            ),
            "workflow_md": (
                "1. Onboard new users and assign roles.\n"
                "2. Tune field rules based on office policies.\n"
                "3. Review validation logs for recurring data issues.\n"
            ),
        },
        "accounts": {
            "title": "Accounts — bill processing & payments",
            "responsibilities_md": (
                "- Register and verify vendor bills.\n"
                "- Track bill status and payment progress.\n"
                "- Generate GST and payment reports.\n"
            ),
            "workflow_md": (
                "1. Search vendor → register new bill.\n"
                "2. Track approvals and mark bills as paid.\n"
                "3. Review GST and payment summary reports.\n"
            ),
        },
        "inventory_manager": {
            "title": "Inventory — stock & items",
            "responsibilities_md": (
                "- Maintain item master and categories.\n"
                "- Approve stock-related bills.\n"
                "- Monitor stock lots, low stock, and issues.\n"
            ),
            "workflow_md": (
                "1. Keep item master and categories up to date.\n"
                "2. After bill approval, verify created stock lots.\n"
                "3. Monitor low-stock alerts and coordinate replenishment.\n"
            ),
        },
        "store_keeper": {
            "title": "Store keeper — issues & returns",
            "responsibilities_md": (
                "- Issue items to employees.\n"
                "- Record returns, damage, and losses.\n"
                "- Keep physical and system stock in sync.\n"
            ),
            "workflow_md": (
                "1. Locate available lots for requested items.\n"
                "2. Issue items to employees and print records if needed.\n"
                "3. Record returns or mark as lost/damaged promptly.\n"
            ),
        },
        "staff_viewer": {
            "title": "Staff / Viewer — read-only access",
            "responsibilities_md": (
                "- View status of own requests and inventory usage.\n"
                "- Consult reports and dashboards as permitted.\n"
            ),
            "workflow_md": (
                "1. Use dashboards to understand current status.\n"
                "2. Use reports for reference; request changes via authorized staff.\n"
            ),
        },
    }
    for role_name, payload in defaults.items():
        if not RoleGuidance.query.filter_by(role_name=role_name).first():
            db.session.add(
                RoleGuidance(
                    role_name=role_name,
                    title=payload["title"],
                    responsibilities_md=payload["responsibilities_md"],
                    workflow_md=payload["workflow_md"],
                    modules_json=None,
                )
            )
    if not Announcement.query.first():
        db.session.add(
            Announcement(
                title="Welcome to the IIA Vendor Bill & Inventory System",
                body=(
                    "This system centralises vendor bills, inventory, and approvals for "
                    "IIA – VBO Kavalur. Use the About Me page to understand your role-specific "
                    "responsibilities and quick links."
                ),
                audience_role=None,
            )
        )
    db.session.commit()


def init_database(app):
    """
    Create all ORM tables if missing, then seed defaults in non-production.

    Avoids OperationalError when SQLite file exists but migrations/CLI
    were not run yet.
    """
    with app.app_context():
        db.create_all()
        if os.environ.get("FLASK_ENV", "development") == "production":
            return
        run_seed()
        app.logger.debug("Database bootstrap: create_all + dev seed (non-production).")
