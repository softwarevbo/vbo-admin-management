"""Human-readable sequential numbers."""
from datetime import datetime, timezone

from app.extensions import db
from app.models.inventory import SequenceNumber


def _next_sequence(name: str) -> int:
    year = datetime.now(timezone.utc).year
    q = SequenceNumber.query.filter_by(name=name, year=year)
    bind = db.session.get_bind()
    if bind is not None and bind.dialect.name != "sqlite":
        q = q.with_for_update()
    seq = q.first()
    if seq is None:
        seq = SequenceNumber(name=name, year=year, last_value=0)
        db.session.add(seq)
        db.session.flush()
    seq.last_value += 1
    db.session.flush()
    return seq.last_value


def next_bill_register_no() -> str:
    n = _next_sequence("bill_register")
    year = datetime.now(timezone.utc).year
    return f"BR/VBO/{year}/{n:05d}"


def next_issue_code() -> str:
    n = _next_sequence("issue_register")
    year = datetime.now(timezone.utc).year
    return f"IS/VBO/{year}/{n:05d}"
