"""Per-module form field requirement and uniqueness rules (admin-configurable)."""
from datetime import datetime, timezone

from app.extensions import db


class FormFieldRule(db.Model):
    __tablename__ = "form_field_rules"

    id = db.Column(db.Integer, primary_key=True)
    module = db.Column(db.String(64), nullable=False, index=True)
    field_key = db.Column(db.String(80), nullable=False)
    is_required = db.Column(db.Boolean, default=False, nullable=False)
    check_unique = db.Column(db.Boolean, default=False, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (db.UniqueConstraint("module", "field_key", name="uq_form_field_module_key"),)


class FormFieldConfig(db.Model):
    """Field visibility, label overrides and ordering (admin-configurable)."""

    __tablename__ = "form_field_configs"

    id = db.Column(db.Integer, primary_key=True)
    module = db.Column(db.String(64), nullable=False, index=True)
    field_key = db.Column(db.String(80), nullable=False)
    is_visible = db.Column(db.Boolean, default=True, nullable=False)
    label_override = db.Column(db.String(200))
    order_index = db.Column(db.Integer, default=0, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        db.UniqueConstraint("module", "field_key", name="uq_form_field_cfg_module_key"),
    )


class ValidationLog(db.Model):
    """Server-side validation outcomes for debugging."""

    __tablename__ = "validation_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    module = db.Column(db.String(64), index=True)
    form_name = db.Column(db.String(120))
    success = db.Column(db.Boolean, default=False, nullable=False)
    errors = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    user = db.relationship("User")
