"""Load and apply admin-configured field rules."""
from flask import request
from flask_login import current_user

from app.field_definitions import (
    ALL_MODULES,
    FIELD_REGISTRY,
    DEFAULT_UNIQUE_FIELDS,
)
from app.extensions import db
from app.models.form_field_rule import FormFieldConfig, FormFieldRule, ValidationLog


def get_rules_for_module(module: str) -> dict[str, dict]:
    """
    Returns { field_key: {"required": bool, "unique": bool, "visible": bool, "label": str|None, "order": int} }
    Merges DB rows with registry: missing rows default to required=False, unique=False
    unless implied by DEFAULT_UNIQUE_FIELDS for first-time UX.
    """
    if module not in FIELD_REGISTRY:
        return {}
    allowed_keys = {f["key"] for f in FIELD_REGISTRY[module]}
    rows = FormFieldRule.query.filter_by(module=module).all()
    by_key = {r.field_key: r for r in rows}
    cfg_rows = FormFieldConfig.query.filter_by(module=module).all()
    cfg_by_key = {c.field_key: c for c in cfg_rows}
    defaults_unique = set(DEFAULT_UNIQUE_FIELDS.get(module, ()))
    out = {}
    for key in allowed_keys:
        cfg = cfg_by_key.get(key)
        if key in by_key:
            r = by_key[key]
            out[key] = {
                "required": r.is_required,
                "unique": r.check_unique,
                "visible": True if cfg is None else bool(cfg.is_visible),
                "label": None if cfg is None else cfg.label_override,
                "order": 0 if cfg is None else int(cfg.order_index or 0),
            }
        else:
            out[key] = {
                "required": False,
                "unique": key in defaults_unique,
                "visible": True if cfg is None else bool(cfg.is_visible),
                "label": None if cfg is None else cfg.label_override,
                "order": 0 if cfg is None else int(cfg.order_index or 0),
            }
    return out


def get_field_view(module: str) -> list[dict]:
    """Ordered field list for templates (visibility + label overrides)."""
    rules = get_rules_for_module(module)
    if module not in FIELD_REGISTRY:
        return []
    rows = []
    # Base label from registry; override if configured
    for idx, fm in enumerate(FIELD_REGISTRY[module]):
        key = fm["key"]
        r = rules.get(key, {})
        label = r.get("label") or fm["label"]
        rows.append(
            {
                "key": key,
                "label": label,
                "required": bool(r.get("required")),
                "unique": bool(r.get("unique")),
                "visible": bool(r.get("visible", True)),
                "order": int(r.get("order") or idx),
            }
        )
    rows.sort(key=lambda x: (x["order"], x["label"]))
    return rows


def seed_default_rules():
    """Insert default rule rows (all optional; unique flags from DEFAULT_UNIQUE_FIELDS)."""
    for module in ALL_MODULES:
        if module not in FIELD_REGISTRY:
            continue
        defaults_unique = set(DEFAULT_UNIQUE_FIELDS.get(module, ()))
        for order_index, fm in enumerate(FIELD_REGISTRY[module]):
            key = fm["key"]
            exists = FormFieldRule.query.filter_by(module=module, field_key=key).first()
            if exists:
                continue
            db.session.add(
                FormFieldRule(
                    module=module,
                    field_key=key,
                    is_required=False,
                    check_unique=key in defaults_unique,
                )
            )
            if not FormFieldConfig.query.filter_by(module=module, field_key=key).first():
                db.session.add(
                    FormFieldConfig(
                        module=module,
                        field_key=key,
                        is_visible=True,
                        label_override=None,
                        order_index=order_index,
                    )
                )
    db.session.commit()


def save_rules_from_form(module: str, form_data) -> None:
    """
    form_data: werkzeug MultiDict or dict.
    Checkbox names: required_<field_key>, unique_<field_key> with value 1 when checked.
    """
    if module not in FIELD_REGISTRY:
        return

    def _on(key: str) -> bool:
        v = form_data.get(key)
        if v is None:
            return False
        s = str(v).lower()
        return s in ("1", "on", "true", "yes")

    for fm in FIELD_REGISTRY[module]:
        key = fm["key"]
        req = _on(f"required_{key}")
        uniq = _on(f"unique_{key}")
        vis = _on(f"visible_{key}") or False
        label_override = (form_data.get(f"label_{key}") or "").strip() or None
        order_val = form_data.get(f"order_{key}")
        try:
            order_index = int(order_val) if order_val not in (None, "") else 0
        except ValueError:
            order_index = 0
        row = FormFieldRule.query.filter_by(module=module, field_key=key).first()
        if not row:
            row = FormFieldRule(module=module, field_key=key)
            db.session.add(row)
        row.is_required = req
        row.check_unique = uniq
        cfg = FormFieldConfig.query.filter_by(module=module, field_key=key).first()
        if not cfg:
            cfg = FormFieldConfig(module=module, field_key=key)
            db.session.add(cfg)
        cfg.is_visible = vis
        cfg.label_override = label_override
        cfg.order_index = order_index
    db.session.commit()


def log_validation(
    module: str,
    form_name: str,
    success: bool,
    errors: dict | None = None,
):
    uid = current_user.id if current_user.is_authenticated else None
    ip = request.remote_addr if request else None
    db.session.add(
        ValidationLog(
            user_id=uid,
            module=module,
            form_name=form_name,
            success=success,
            errors=errors or {},
            ip_address=ip,
        )
    )
    db.session.commit()
