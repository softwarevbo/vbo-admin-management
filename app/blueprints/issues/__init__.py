from decimal import Decimal

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.field_definitions import MODULE_ISSUE
from app.constants import (
    ROLE_ADMIN,
    ROLE_INVENTORY_MANAGER,
    ROLE_STORE_KEEPER,
    ROLE_STAFF_VIEWER,
    ROLE_SUPER_ADMIN,
)
from app.extensions import db
from app.forms.issue import ItemIssueForm, ItemReturnForm
from app.models.employee import Employee
from app.models.inventory import ItemIssue, StockLot
from app.services import issue_service
from app.services.field_rules_service import get_field_view, get_rules_for_module
from app.utils.dynamic_forms import apply_rules_to_form, validate_submission

bp = Blueprint("issues", __name__)


@bp.before_request
@login_required
def _auth():
    pass


def _can_issue():
    return current_user.role.name in (
        ROLE_SUPER_ADMIN,
        ROLE_ADMIN,
        ROLE_INVENTORY_MANAGER,
        ROLE_STORE_KEEPER,
    )


@bp.route("/")
def list_issues():
    rows = (
        ItemIssue.query.filter(ItemIssue.deleted_at.is_(None))
        .order_by(ItemIssue.created_at.desc())
        .limit(300)
        .all()
    )
    return render_template("issues/list.html", rows=rows, can_issue=_can_issue())


@bp.route("/new", methods=["GET", "POST"])
def new_issue():
    if current_user.role.name == ROLE_STAFF_VIEWER:
        flash("Read-only.", "danger")
        return redirect(url_for("issues.list_issues"))
    if not _can_issue():
        flash("Permission denied.", "danger")
        return redirect(url_for("issues.list_issues"))
    form = ItemIssueForm()
    form.employee_id.choices = [
        (e.id, f"{e.employee_code} — {e.employee_name}")
        for e in Employee.query.filter(Employee.deleted_at.is_(None))
        .order_by(Employee.employee_name)
        .limit(2000)
        .all()
    ]
    if not form.employee_id.choices:
        flash("Create at least one employee before issuing stock.", "warning")
        return redirect(url_for("employees.new_employee"))
    rules = get_rules_for_module(MODULE_ISSUE)
    apply_rules_to_form(form, rules)
    for row in get_field_view(MODULE_ISSUE):
        if row.get("label") and hasattr(form, row["key"]):
            getattr(form, row["key"]).label.text = row["label"]
    lots = (
        StockLot.query.filter(
            StockLot.deleted_at.is_(None), StockLot.quantity_available > 0
        )
        .order_by(StockLot.id.desc())
        .limit(200)
        .all()
    )
    if request.method == "POST" and validate_submission(
        form, MODULE_ISSUE, "issue_create", duplicate_checker=None
    ):
        lot_ids = request.form.getlist("lot_id")
        qtys = request.form.getlist("qty")
        lines = []
        for lid, q in zip(lot_ids, qtys):
            if not lid or not (q and str(q).strip()):
                continue
            lines.append({"stock_lot_id": int(lid), "quantity": Decimal(str(q))})
        if not lines:
            flash(
                "Add at least one stock line with a quantity greater than zero.",
                "danger",
            )
            return render_template(
                "issues/form.html",
                form=form,
                lots=lots,
                field_rules=rules,
                module=MODULE_ISSUE,
                field_view=get_field_view(MODULE_ISSUE),
            )
        try:
            issue = issue_service.create_issue(
                form.employee_id.data,
                form.issue_date.data,
                lines,
                remarks=form.remarks.data,
            )
            db.session.commit()
            flash(f"Issue {issue.issue_code} created successfully.", "success")
            return redirect(url_for("issues.issue_detail", iid=issue.id))
        except Exception as exc:
            db.session.rollback()
            flash(str(exc), "danger")
    return render_template(
        "issues/form.html",
        form=form,
        lots=lots,
        field_rules=rules,
        module=MODULE_ISSUE,
        field_view=get_field_view(MODULE_ISSUE),
    )


@bp.route("/<int:iid>", methods=["GET", "POST"])
def issue_detail(iid):
    issue = ItemIssue.query.filter_by(id=iid, deleted_at=None).first_or_404()
    form = ItemReturnForm()
    if request.method == "POST" and form.validate_on_submit() and _can_issue():
        line_ids = request.form.getlist("issue_line_id")
        qtys = request.form.getlist("return_qty")
        conds = request.form.getlist("item_condition")
        line_returns = []
        for lid, q, c in zip(line_ids, qtys, conds):
            if not lid or not q:
                continue
            line_returns.append(
                {
                    "issue_line_id": int(lid),
                    "return_qty": Decimal(str(q)),
                    "item_condition": c or "good",
                }
            )
        if line_returns:
            try:
                issue_service.return_lines(issue, line_returns)
                db.session.commit()
                flash("Return processed successfully.", "success")
            except Exception as exc:
                db.session.rollback()
                flash(str(exc), "danger")
        return redirect(url_for("issues.issue_detail", iid=iid))
    return render_template("issues/detail.html", issue=issue, form=form)
