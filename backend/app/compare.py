"""Pure comparison logic: decide where System A and System B disagree.

Takes plain dicts in, plain dicts out - no DB session, no ORM objects - so it can be
tested without a database.
"""
from app.parsing import normalize_ref

VALUE_TOLERANCE = 0.01
VOIDED = "VOIDED"

MISSING_IN_B = "missing_in_b"
ORPHAN_REF = "orphan_ref"
DUPLICATE_IN_B = "duplicate_in_b"
DUPLICATE_IN_A = "duplicate_in_a"
VALUE_MISMATCH = "value_mismatch"
VOIDED_IN_A = "voided_in_a"


def _match_key(raw, side, index):
    """Bucket a row by its normalized reference.

    A reference that will not normalize still gets a key of its own rather than
    collapsing into a shared `None` bucket - otherwise every unparseable reference on
    both sides would appear to match every other one. A blank reference matches
    nothing at all, not even another blank.
    """
    ref = normalize_ref(raw)
    if ref:
        return ref
    text = (raw or "").strip()
    if text:
        return ("unnormalized", text.upper())
    return ("blank", side, index)


def _group(rows, ref_field, side):
    grouped = {}
    for index, row in enumerate(rows):
        grouped.setdefault(_match_key(row[ref_field], side, index), []).append(row)
    return grouped


def _values_agree(a_value, b_value):
    if a_value is None or b_value is None:
        return a_value is None and b_value is None
    return abs(a_value - b_value) <= VALUE_TOLERANCE


def _is_split(a_row, entries):
    """True when several System B entries add up to System A's total.

    That is a record entered in parts, not entered twice - the data labels one such
    entry "Entry part 2 of 2". Decided on the arithmetic, not the label, because the
    label is free text. If any value is unparseable the split cannot be proven, so
    the record falls back to being reported as a duplicate.

    ponytail: a sum is weak evidence - a genuine double entry of a record whose value is
    exactly half would pass as a split. Upgrade path is a part-of field in System B; this
    export has none.
    """
    if a_row["total_value"] is None or any(e["value"] is None for e in entries):
        return False
    return abs(sum(e["value"] for e in entries) - a_row["total_value"]) <= VALUE_TOLERANCE


def find_disagreements(system_a_rows, system_b_rows):
    """
    system_a_rows: dicts with record_id, location_id, total_value, total_value_raw, state
    system_b_rows: dicts with entry_id, record_ref_raw, location_id, value, value_raw

    Returns a list of disagreement dicts:
        reason, record_ref, location_id, system_a_value, system_b_value, entry_ids

    One reason per record: the first thing that is wrong with it is what gets reported.
    """
    a_by_ref = _group(system_a_rows, "record_id", "a")
    b_by_ref = _group(system_b_rows, "record_ref_raw", "b")

    disagreements = []

    for key, entries in b_by_ref.items():
        if key in a_by_ref:
            continue
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

    for key, a_rows in a_by_ref.items():
        entries = b_by_ref.get(key, [])

        # Two System A records claiming one reference: there is no single row left to
        # compare against, so report the ambiguity itself and stop there.
        if len(a_rows) > 1:
            disagreements.append(
                {
                    "reason": DUPLICATE_IN_A,
                    "record_ref": a_rows[0]["record_id"],
                    "location_id": a_rows[0]["location_id"],
                    "system_a_value": "; ".join(r["total_value_raw"] for r in a_rows),
                    "system_b_value": "; ".join(e["value_raw"] for e in entries) or None,
                    "entry_ids": [e["entry_id"] for e in entries],
                }
            )
            continue

        a_row = a_rows[0]
        voided = (a_row.get("state") or "").strip().upper() == VOIDED

        if len(entries) == 0 and not voided:
            # A voided record with no entry in System B is the expected outcome, not a
            # disagreement - so this branch is skipped entirely when the record is voided.
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
        elif len(entries) == 0:
            pass  # voided and absent from System B: nothing to report
        elif voided:
            # System A voided the record but System B still carries an entry for it:
            # the two systems disagree about whether the event stands at all.
            disagreements.append(
                {
                    "reason": VOIDED_IN_A,
                    "record_ref": a_row["record_id"],
                    "location_id": a_row["location_id"],
                    "system_a_value": a_row["total_value_raw"],
                    "system_b_value": "; ".join(e["value_raw"] for e in entries),
                    "entry_ids": [e["entry_id"] for e in entries],
                }
            )
        elif len(entries) > 1 and not _is_split(a_row, entries):
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
        elif len(entries) == 1:
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
