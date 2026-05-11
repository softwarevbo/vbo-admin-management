from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from app.field_definitions import MODULE_CATEGORY, MODULE_ITEM
from app.constants import ROLE_ADMIN, ROLE_INVENTORY_MANAGER, ROLE_SUPER_ADMIN
from app.extensions import db
from app.forms.item import CategoryForm, ItemMasterForm
from app.models.inventory import Category, ItemMaster, StockLot
from app.services import audit_service
from app.services.duplicate_check_service import category_duplicate_errors, item_duplicate_errors
from app.services.field_rules_service import get_field_view, get_rules_for_module
from app.utils.decorators import role_required
from app.utils.dynamic_forms import apply_rules_to_form, validate_submission

bp = Blueprint("inventory", __name__)


@bp.before_request
@login_required
def _auth():
    pass


def _can_edit():
    return current_user.role.name in (
        ROLE_SUPER_ADMIN,
        ROLE_ADMIN,
        ROLE_INVENTORY_MANAGER,
    )


@bp.route("/items")
def list_items():
    items = (
        ItemMaster.query.filter(ItemMaster.deleted_at.is_(None))
        .order_by(ItemMaster.item_name)
        .limit(1000)
        .all()
    )
    avail = dict(
        db.session.query(StockLot.item_master_id, func.sum(StockLot.quantity_available))
        .filter(StockLot.deleted_at.is_(None))
        .group_by(StockLot.item_master_id)
        .all()
    )
    stock_map = {int(k): float(v or 0) for k, v in avail}
    return render_template(
        "inventory/items.html",
        items=items,
        stock_map=stock_map,
        can_edit=_can_edit(),
    )


@bp.route("/items/new", methods=["GET", "POST"])
@role_required(ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_INVENTORY_MANAGER)
def new_item():
    form = ItemMasterForm()
    form.category_id.choices = [(0, "—")] + [
        (c.id, c.name) for c in Category.query.order_by(Category.name).all()
    ]
    rules = get_rules_for_module(MODULE_ITEM)
    apply_rules_to_form(form, rules)
    for row in get_field_view(MODULE_ITEM):
        if row.get("label") and hasattr(form, row["key"]):
            getattr(form, row["key"]).label.text = row["label"]
    if validate_submission(
        form,
        MODULE_ITEM,
        "item_create",
        duplicate_checker=lambda: item_duplicate_errors(form, exclude_item_id=None),
    ):
        it = ItemMaster()
        form.populate_obj(it)
        it.item_code = form.item_code.data.strip() if form.item_code.data else ""
        it.item_name = form.item_name.data.strip() if form.item_name.data else ""
        if form.category_id.data == 0:
            it.category_id = None
        db.session.add(it)
        db.session.commit()
        audit_service.log_action("item_create", entity_type="item_master", entity_id=it.id)
        db.session.commit()
        flash("Item saved successfully.", "success")
        return redirect(url_for("inventory.list_items"))
    return render_template(
        "inventory/item_form.html",
        form=form,
        item=None,
        field_rules=rules,
        module=MODULE_ITEM,
        field_view=get_field_view(MODULE_ITEM),
    )


@bp.route("/items/<int:iid>/edit", methods=["GET", "POST"])
def edit_item(iid):
    if not _can_edit():
        flash("Permission denied.", "danger")
        return redirect(url_for("inventory.list_items"))
    item = ItemMaster.query.filter_by(id=iid, deleted_at=None).first_or_404()
    form = ItemMasterForm(obj=item)
    form.category_id.choices = [(0, "—")] + [
        (c.id, c.name) for c in Category.query.order_by(Category.name).all()
    ]
    rules = get_rules_for_module(MODULE_ITEM)
    apply_rules_to_form(form, rules)
    for row in get_field_view(MODULE_ITEM):
        if row.get("label") and hasattr(form, row["key"]):
            getattr(form, row["key"]).label.text = row["label"]
    if validate_submission(
        form,
        MODULE_ITEM,
        "item_update",
        duplicate_checker=lambda: item_duplicate_errors(form, exclude_item_id=item.id),
    ):
        form.populate_obj(item)
        item.item_code = form.item_code.data.strip() if form.item_code.data else ""
        item.item_name = form.item_name.data.strip() if form.item_name.data else ""
        if form.category_id.data == 0:
            item.category_id = None
        db.session.commit()
        flash("Item updated successfully.", "success")
        return redirect(url_for("inventory.list_items"))
    return render_template(
        "inventory/item_form.html",
        form=form,
        item=item,
        field_rules=rules,
        module=MODULE_ITEM,
        field_view=get_field_view(MODULE_ITEM),
    )


@bp.route("/categories", methods=["GET", "POST"])
@role_required(ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_INVENTORY_MANAGER)
def categories():
    form = CategoryForm()
    rows = Category.query.order_by(Category.name).all()
    rules = get_rules_for_module(MODULE_CATEGORY)
    apply_rules_to_form(form, rules)
    for row in get_field_view(MODULE_CATEGORY):
        if row.get("label") and hasattr(form, row["key"]):
            getattr(form, row["key"]).label.text = row["label"]
    if validate_submission(
        form,
        MODULE_CATEGORY,
        "category_create",
        duplicate_checker=lambda: category_duplicate_errors(form, exclude_category_id=None),
    ):
        db.session.add(
            Category(
                name=form.name.data.strip() if form.name.data else "",
                description=form.description.data,
            )
        )
        db.session.commit()
        flash("Category added successfully.", "success")
        return redirect(url_for("inventory.categories"))
    return render_template(
        "inventory/categories.html",
        form=form,
        rows=rows,
        field_rules=rules,
        module=MODULE_CATEGORY,
        field_view=get_field_view(MODULE_CATEGORY),
    )


@bp.route("/stock-lots")
def stock_lots():
    lots = (
        StockLot.query.filter(StockLot.deleted_at.is_(None))
        .order_by(StockLot.id.desc())
        .limit(500)
        .all()
    )
    return render_template("inventory/stock_lots.html", lots=lots)
