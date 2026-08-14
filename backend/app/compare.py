"""Pure comparison logic: decide where System A and System B disagree.

Takes plain dicts in, plain dicts out - no DB session, no ORM objects - so it can be
tested without a database.
"""
from app.parsing import normalize_ref

VALUE_TOLERANCE = 0.01

MISSING_IN_B = "missing_in_b"
ORPHAN_REF = "orphan_ref"
DUPLICATE_IN_B = "duplicate_in_b"
VALUE_MISMATCH = "value_mismatch"


def _values_agree(a_value, b_value):
    if a_value is None or b_value is None:
        return a_value is None and b_value is None
    return abs(a_value - b_value) <= VALUE_TOLERANCE


def find_disagreements(system_a_rows, system_b_rows):
    """
    system_a_rows: iterable of dicts with record_id, location_id, total_value, total_value_raw
    system_b_rows: iterable of dicts with entry_id, record_ref_raw, location_id, value, value_raw

    Returns a list of disagreement dicts:
        reason, record_ref, location_id, system_a_value, system_b_value, entry_ids
    """
    a_by_ref = {normalize_ref(r["record_id"]): r for r in system_a_rows}

    b_by_ref = {}
    for entry in system_b_rows:
        ref = normalize_ref(entry["record_ref_raw"])
        b_by_ref.setdefault(ref, []).append(entry)

    disagreements = []

    for ref, entries in b_by_ref.items():
        if ref not in a_by_ref:
            for entry in entries:
                disagreements.append(
                    {
                        "reason": ORPHAN_REF,
                        "record_ref": entry["record_ref_raw"],
                        "location_id": entry["location_id"],
                        "system_a_value": None,
                        "system_b_value": entry["value_raw"],
                        "entry_ids": [entry["entry_id"]],
                    }
                )

    for ref, a_row in a_by_ref.items():
        entries = b_by_ref.get(ref, [])

        if len(entries) == 0:
            disagreements.append(
                {
                    "reason": MISSING_IN_B,
                    "record_ref": a_row["record_id"],
                    "location_id": a_row["location_id"],
                    "system_a_value": a_row["total_value_raw"],
                    "system_b_value": None,
                    "entry_ids": [],
                }
            )
        elif len(entries) > 1:
            disagreements.append(
                {
                    "reason": DUPLICATE_IN_B,
                    "record_ref": a_row["record_id"],
                    "location_id": a_row["location_id"],
                    "system_a_value": a_row["total_value_raw"],
                    "system_b_value": "; ".join(e["value_raw"] for e in entries),
                    "entry_ids": [e["entry_id"] for e in entries],
                }
            )
        else:
            entry = entries[0]
            if not _values_agree(a_row["total_value"], entry["value"]):
                disagreements.append(
                    {
                        "reason": VALUE_MISMATCH,
                        "record_ref": a_row["record_id"],
                        "location_id": a_row["location_id"],
                        "system_a_value": a_row["total_value_raw"],
                        "system_b_value": entry["value_raw"],
                        "entry_ids": [entry["entry_id"]],
                    }
                )

    return disagreements
