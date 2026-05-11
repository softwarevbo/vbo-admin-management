from flask import Blueprint, jsonify, request
from flask_login import login_required

from app.field_definitions import ALL_MODULES, FIELD_REGISTRY, MODULE_LABELS
from app.models.vendor import Vendor
from app.services.field_rules_service import get_rules_for_module
from app.services.field_validation_api import check_field_remote

bp = Blueprint("api", __name__)


@bp.route("/vendors/search")
@login_required
def vendors_search():
    q = request.args.get("q", "").strip()
    query = Vendor.query.filter(Vendor.deleted_at.is_(None))
    if q:
        like = f"%{q}%"
        query = query.filter(
            (Vendor.vendor_name.ilike(like)) | (Vendor.vendor_code.ilike(like))
        )
    rows = query.order_by(Vendor.vendor_name).limit(50).all()
    return jsonify(
        {
            "data": [
                {
                    "id": v.id,
                    "code": v.vendor_code,
                    "name": v.vendor_name,
                    "gstin": v.gstin_number,
                }
                for v in rows
            ]
        }
    )


@bp.route("/field-rules/<module>")
@login_required
def field_rules_json(module):
    """JSON rules for SPA / debugging."""
    if module not in FIELD_REGISTRY:
        return jsonify({"error": "unknown module"}), 404
    return jsonify({"module": module, "rules": get_rules_for_module(module)})


@bp.route("/validate-field")
@login_required
def validate_field():
    """Duplicate / uniqueness preview (GET; login + same-site policy)."""
    module = (request.args.get("module") or "").strip()
    field = (request.args.get("field") or "").strip()
    value = request.args.get("value", "")
    exclude_id = request.args.get("exclude_id", type=int)
    exclude_bill_id = request.args.get("exclude_bill_id", type=int)
    vendor_id = request.args.get("vendor_id", type=int)
    if module not in FIELD_REGISTRY:
        return jsonify({"valid": True, "message": ""})
    if field not in {f["key"] for f in FIELD_REGISTRY[module]}:
        return jsonify({"valid": True, "message": ""})
    ok, msg = check_field_remote(
        module,
        field,
        value,
        exclude_id=exclude_id,
        exclude_bill_id=exclude_bill_id,
        vendor_id=vendor_id,
    )
    return jsonify({"valid": ok, "message": msg})
