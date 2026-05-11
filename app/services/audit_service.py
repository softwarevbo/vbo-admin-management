"""Centralized audit logging."""
from flask import request
from flask_login import current_user

from app.extensions import db
from app.models.audit import AuditLog, Notification


def log_action(
    action: str,
    entity_type: str | None = None,
    entity_id: int | None = None,
    details: dict | None = None,
    user_id: int | None = None,
):
    uid = user_id
    if uid is None and current_user.is_authenticated:
        uid = current_user.id
    ip = request.remote_addr if request else None
    row = AuditLog(
        user_id=uid,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details or {},
        ip_address=ip,
    )
    db.session.add(row)


def notify_user(user_id: int, type_: str, title: str, message: str, **kwargs):
    db.session.add(
        Notification(
            user_id=user_id,
            type=type_,
            title=title,
            message=message,
            related_type=kwargs.get("related_type"),
            related_id=kwargs.get("related_id"),
        )
    )
