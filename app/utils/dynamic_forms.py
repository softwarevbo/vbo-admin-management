"""Apply database-driven required/optional rules to WTForms instances."""
from flask import request
from wtforms import BooleanField, FileField, SelectField
from wtforms.validators import DataRequired, InputRequired, Optional

from app.services.field_rules_service import log_validation


def _strip_optional_datarequired(validators):
    out = []
    for v in validators:
        if type(v).__name__ in ("Optional", "DataRequired", "InputRequired"):
            continue
        out.append(v)
    return out


def _label_text(field) -> str:
    return field.label.text if field.label else field.name


def apply_rules_to_form(form, rules: dict[str, dict]) -> None:
    """
    Mutate validators on each field listed in rules.
    """
    for field_name, meta in rules.items():
        if not hasattr(form, field_name):
            continue
        field = getattr(form, field_name)
        base = _strip_optional_datarequired(field.validators)
        required = meta.get("required", False)
        msg = f"{_label_text(field)} is required."
        if isinstance(field, BooleanField):
            field.validators = (
                [InputRequired(message=msg)] + base if required else [Optional()] + base
            )
        elif isinstance(field, FileField):
            field.validators = (
                [DataRequired(message=msg)] + base if required else [Optional()] + base
            )
        elif isinstance(field, SelectField) and getattr(field, "coerce", None) == int:
            if required:
                field.validators = [DataRequired(message=msg), *base]
            else:
                field.validators = [Optional(), *base]
        else:
            if required:
                field.validators = [DataRequired(message=msg), *base]
            else:
                field.validators = [Optional(), *base]


def validate_submission(
    form,
    module: str,
    form_name: str,
    *,
    duplicate_checker=None,
) -> bool:
    """
    Run WTForms validation, optional duplicate checker (mutates form field errors),
    and write validation_logs. Returns True if OK to proceed with save.
    """
    if request.method != "POST":
        return False
    if not form.validate_on_submit():
        log_validation(
            module,
            form_name,
            success=False,
            errors={k: list(v) for k, v in form.errors.items()},
        )
        return False
    if duplicate_checker:
        duplicate_checker()
        if form.errors:
            log_validation(
                module,
                form_name,
                success=False,
                errors={k: list(v) for k, v in form.errors.items()},
            )
            return False
    log_validation(module, form_name, success=True, errors={})
    return True
