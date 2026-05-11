"""GSTIN / IFSC pattern checks (lightweight; not legal certification)."""
import re

GSTIN_PATTERN = re.compile(
    r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
)
IFSC_PATTERN = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")


def is_valid_gstin(value: str | None) -> bool:
    if not value:
        return True
    v = value.strip().upper()
    return bool(GSTIN_PATTERN.match(v))


def is_valid_ifsc(value: str | None) -> bool:
    if not value:
        return True
    v = value.strip().upper()
    return bool(IFSC_PATTERN.match(v))
