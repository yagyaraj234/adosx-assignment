"""Helpers for coping with dirty CSV input. Never raise on bad data - return None."""
import re


def parse_number(raw: str | None) -> float | None:
    """Parse a money value, tolerating thousands separators, blanks, and junk."""
    if raw is None:
        return None
    cleaned = raw.strip().replace(",", "")
    if cleaned == "":
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def normalize_ref(raw: str | None) -> str | None:
    """Canonicalize a record reference: 'rec1034', 'REC1034', ' REC-1034 ' -> 'REC-1034'."""
    if raw is None:
        return None
    cleaned = raw.strip().upper().replace("-", "").replace("_", "").replace(" ", "")
    match = re.match(r"^REC(\d+)$", cleaned)
    if not match:
        return None
    return f"REC-{match.group(1)}"
