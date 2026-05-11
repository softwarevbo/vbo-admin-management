from flask import Blueprint, render_template
from flask_login import login_required

from app.services.dashboard_service import get_summary

bp = Blueprint("main", __name__)


@bp.route("/")
@login_required
def index():
    return dashboard()


@bp.route("/dashboard")
@login_required
def dashboard():
    data = get_summary()
    return render_template("main/dashboard.html", **data)
