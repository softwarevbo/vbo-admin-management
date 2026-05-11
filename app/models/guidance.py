"""Models for role-based user guidance and announcements."""
from datetime import datetime, timezone

from app.extensions import db


class RoleGuidance(db.Model):
    """High-level responsibilities and workflow text per role."""

    __tablename__ = "role_guidance"

    id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(64), unique=True, nullable=False, index=True)
    title = db.Column(db.String(160), nullable=False)
    responsibilities_md = db.Column(db.Text)  # Markdown / long text
    workflow_md = db.Column(db.Text)
    modules_json = db.Column(db.JSON)  # list of {name, description, endpoint, actions}
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class Announcement(db.Model):
    """System announcements shown on dashboard / About Me."""

    __tablename__ = "announcements"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    audience_role = db.Column(db.String(64))  # None / empty => all roles
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))

    creator = db.relationship("User")

