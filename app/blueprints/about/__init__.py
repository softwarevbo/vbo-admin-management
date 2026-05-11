from flask import Blueprint, render_template
from flask_login import login_required

from app.services.guidance_service import (
    get_announcements_for_user,
    get_role_profile,
    get_user_summary,
)

bp = Blueprint("about", __name__, url_prefix="/about")


@bp.before_request
@login_required
def _auth():
    # All logged-in users can see their own guidance page
    return None


@bp.route("/me")
def about_me():
    profile = get_role_profile()
    summary = get_user_summary()
    announcements = get_announcements_for_user()
    return render_template(
        "about/me.html",
        profile=profile,
        summary=summary,
        announcements=announcements,
    )

