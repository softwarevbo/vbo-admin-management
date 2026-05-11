"""Bills, line items, stock lots, issues, categories, item master."""
from datetime import datetime, timezone

from app.extensions import db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    items = db.relationship("ItemMaster", back_populates="category")


class ItemMaster(db.Model):
    """Catalog SKU; stock is aggregated from stock lots."""

    __tablename__ = "item_master"

    id = db.Column(db.Integer, primary_key=True)
    item_code = db.Column(db.String(64), unique=True, nullable=False, index=True)
    item_name = db.Column(db.String(255), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    description = db.Column(db.Text)
    default_unit = db.Column(db.String(32), default="Nos")
    default_gst_percentage = db.Column(db.Numeric(5, 2), default=18)
    minimum_stock_alert = db.Column(db.Numeric(14, 3), default=0)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    deleted_at = db.Column(db.DateTime)

    category = db.relationship("Category", back_populates="items")
    bill_lines = db.relationship("BillLineItem", back_populates="item_master")
    stock_lots = db.relationship("StockLot", back_populates="item_master")


class SequenceNumber(db.Model):
    """Atomic counters for human-readable numbers."""

    __tablename__ = "sequence_numbers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    last_value = db.Column(db.Integer, nullable=False, default=0)


class VendorBill(db.Model):
    __tablename__ = "vendor_bills"

    id = db.Column(db.Integer, primary_key=True)
    bill_register_no = db.Column(db.String(40), unique=True, index=True)
    vendor_bill_no = db.Column(db.String(80), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey("vendors.id"), nullable=False)
    vendor_bill_date = db.Column(db.Date, nullable=False)
    bill_received_date = db.Column(db.Date)
    processed_date = db.Column(db.Date)
    amount = db.Column(db.Numeric(14, 2), default=0)
    gst_amount = db.Column(db.Numeric(14, 2), default=0)
    total_amount = db.Column(db.Numeric(14, 2), default=0)
    division_section = db.Column(db.String(120))
    indenter_end_user = db.Column(db.String(160))
    bill_status = db.Column(db.String(40), nullable=False, default="pending")
    payment_status = db.Column(db.String(40), default="unpaid")
    payment_date = db.Column(db.Date)
    purchase_order_no = db.Column(db.String(80))
    invoice_file_upload = db.Column(db.String(255))
    remarks = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    approved_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    approval_level_required = db.Column(db.Integer, default=2)
    current_approval_level = db.Column(db.Integer, default=0)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    deleted_at = db.Column(db.DateTime)

    vendor = db.relationship("Vendor", back_populates="bills")
    lines = db.relationship(
        "BillLineItem",
        back_populates="bill",
        cascade="all, delete-orphan",
        order_by="BillLineItem.line_no",
    )
    creator = db.relationship("User", foreign_keys=[created_by])
    approver_user = db.relationship("User", foreign_keys=[approved_by])
    approval_logs = db.relationship(
        "BillApprovalLog", back_populates="bill", order_by="BillApprovalLog.created_at"
    )


class BillLineItem(db.Model):
    """Single line on a vendor bill; stock lots attach here."""

    __tablename__ = "bill_line_items"

    id = db.Column(db.Integer, primary_key=True)
    vendor_bill_id = db.Column(
        db.Integer, db.ForeignKey("vendor_bills.id"), nullable=False, index=True
    )
    line_no = db.Column(db.Integer, nullable=False, default=1)
    item_master_id = db.Column(db.Integer, db.ForeignKey("item_master.id"))
    description = db.Column(db.Text)
    quantity = db.Column(db.Numeric(14, 3), nullable=False)
    unit = db.Column(db.String(32), default="Nos")
    gst_percentage = db.Column(db.Numeric(5, 2), default=18)
    unit_price = db.Column(db.Numeric(14, 4), nullable=False)
    discount = db.Column(db.Numeric(14, 2), default=0)
    line_subtotal = db.Column(db.Numeric(14, 2), default=0)
    gst_amount = db.Column(db.Numeric(14, 2), default=0)
    total_amount = db.Column(db.Numeric(14, 2), default=0)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    bill = db.relationship("VendorBill", back_populates="lines")
    item_master = db.relationship("ItemMaster", back_populates="bill_lines")
    stock_lots = db.relationship(
        "StockLot", back_populates="bill_line", cascade="all, delete-orphan"
    )


class StockLot(db.Model):
    """Inventory lot received against a bill line."""

    __tablename__ = "stock_lots"

    id = db.Column(db.Integer, primary_key=True)
    bill_line_id = db.Column(
        db.Integer, db.ForeignKey("bill_line_items.id"), nullable=False, index=True
    )
    item_master_id = db.Column(
        db.Integer, db.ForeignKey("item_master.id"), nullable=False, index=True
    )
    quantity_received = db.Column(db.Numeric(14, 3), nullable=False)
    quantity_available = db.Column(db.Numeric(14, 3), nullable=False)
    unit_cost = db.Column(db.Numeric(14, 4))
    storage_location = db.Column(db.String(120))
    serial_number = db.Column(db.String(120))
    warranty_period = db.Column(db.String(80))
    expiry_date = db.Column(db.Date)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    deleted_at = db.Column(db.DateTime)

    bill_line = db.relationship("BillLineItem", back_populates="stock_lots")
    item_master = db.relationship("ItemMaster", back_populates="stock_lots")
    movements = db.relationship(
        "StockMovement", back_populates="stock_lot", cascade="all, delete-orphan"
    )
    issue_lines = db.relationship("IssueLine", back_populates="stock_lot")


class StockMovement(db.Model):
    """Audit trail for quantity changes on a lot."""

    __tablename__ = "stock_movements"

    id = db.Column(db.Integer, primary_key=True)
    stock_lot_id = db.Column(
        db.Integer, db.ForeignKey("stock_lots.id"), nullable=False, index=True
    )
    delta_qty = db.Column(db.Numeric(14, 3), nullable=False)
    reason = db.Column(db.String(64), nullable=False)
    reference_type = db.Column(db.String(40))
    reference_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    note = db.Column(db.String(255))
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    stock_lot = db.relationship("StockLot", back_populates="movements")
    user = db.relationship("User")


class ItemIssue(db.Model):
    __tablename__ = "item_issues"

    id = db.Column(db.Integer, primary_key=True)
    issue_code = db.Column(db.String(40), unique=True, index=True)
    employee_id = db.Column(
        db.Integer, db.ForeignKey("employees.id"), nullable=False, index=True
    )
    issued_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    issue_date = db.Column(db.Date, nullable=False)
    expected_return_date = db.Column(db.Date)
    actual_return_date = db.Column(db.Date)
    issue_status = db.Column(db.String(40), default="active")
    approval_status = db.Column(db.String(40), default="pending")
    remarks = db.Column(db.Text)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    deleted_at = db.Column(db.DateTime)

    employee = db.relationship("Employee", back_populates="issues")
    issuer = db.relationship("User", foreign_keys=[issued_by])
    lines = db.relationship(
        "IssueLine", back_populates="item_issue", cascade="all, delete-orphan"
    )


class IssueLine(db.Model):
    __tablename__ = "issue_lines"

    id = db.Column(db.Integer, primary_key=True)
    item_issue_id = db.Column(
        db.Integer, db.ForeignKey("item_issues.id"), nullable=False, index=True
    )
    stock_lot_id = db.Column(
        db.Integer, db.ForeignKey("stock_lots.id"), nullable=False, index=True
    )
    issued_quantity = db.Column(db.Numeric(14, 3), nullable=False)
    returned_quantity = db.Column(db.Numeric(14, 3), default=0)
    item_condition = db.Column(db.String(40))
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    item_issue = db.relationship("ItemIssue", back_populates="lines")
    stock_lot = db.relationship("StockLot", back_populates="issue_lines")


class BillApprovalLog(db.Model):
    __tablename__ = "bill_approval_logs"

    id = db.Column(db.Integer, primary_key=True)
    vendor_bill_id = db.Column(
        db.Integer, db.ForeignKey("vendor_bills.id"), nullable=False, index=True
    )
    level = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(40), nullable=False)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    comments = db.Column(db.Text)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    bill = db.relationship("VendorBill", back_populates="approval_logs")
    actor = db.relationship("User")
