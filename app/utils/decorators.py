"""Route decorators for RBAC."""
from functools import wraps

from flask import abort, current_app
from flask_login import current_user


def role_required(*allowed_roles):
    """Allow access only if current user's role name is in allowed_roles."""

    def decorator(view_fn):
        @wraps(view_fn)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            role_name = (
                current_user.role.name if current_user.role else None
            )
            if role_name not in allowed_roles:
                current_app.logger.warning(
                    "Forbidden: user=%s role=%s needed=%s",
                    current_user.id,
                    role_name,
                    allowed_roles,
                )
                abort(403)
            return view_fn(*args, **kwargs)

        return wrapped

    return decorator
