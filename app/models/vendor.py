"""Vendor master."""
from datetime import datetime, timezone

from app.extensions import db


class Vendor(db.Model):
    __tablename__ = "vendors"

    id = db.Column(db.Integer, primary_key=True)
    vendor_code = db.Column(db.String(32), unique=True, nullable=False, index=True)
    vendor_name = db.Column(db.String(255), nullable=False)
    vendor_company_name = db.Column(db.String(255))
    contact_person = db.Column(db.String(120))
    mobile_number = db.Column(db.String(20))
    email = db.Column(db.String(120))
    gstin_number = db.Column(db.String(20), index=True)
    pan_number = db.Column(db.String(20))
    address = db.Column(db.Text)
    city = db.Column(db.String(80))
    state = db.Column(db.String(80))
    pincode = db.Column(db.String(12))
    country = db.Column(db.String(80), default="India")
    bank_name = db.Column(db.String(120))
    branch_name = db.Column(db.String(120))
    account_holder_name = db.Column(db.String(120))
    account_number = db.Column(db.String(40))
    ifsc_code = db.Column(db.String(20))
    swift_code = db.Column(db.String(20))
    account_type = db.Column(db.String(40))
    upi_id = db.Column(db.String(80))
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

    bills = db.relationship("VendorBill", back_populates="vendor")
