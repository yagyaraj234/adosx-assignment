"""Pure comparison logic: decide where System A and System B disagree.

Takes plain dicts in, plain dicts out - no DB session, no ORM objects - so it can be
tested without a database.

Locations are returned as lists of every location involved on each side. The caller
(the API) is what decides which of them a given tenant is allowed to see; this module
deliberately never filters by org, because a disagreement can straddle two of them.
"""
from app.parsing import normalize_ref

VALUE_TOLERANCE = 0.01
VOIDED = "VOIDED"

MISSING_IN_B = "missing_in_b"
ORPHAN_REF = "orphan_ref"
DUPLICATE_IN_B = "duplicate_in_b"
DUPLICATE_IN_A = "duplicate_in_a"
VALUE_MISMATCH = "value_mismatch"
LOCATION_MISMATCH = "location_mismatch"
VOIDED_IN_A = "voided_in_a"

REASONS = (
    MISSING_IN_B,
    ORPHAN_REF,
    DUPLICATE_IN_B,
    DUPLICATE_IN_A,
    VALUE_MISMATCH,
    LOCATION_MISMATCH,
    VOIDED_IN_A,
)


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


def _disagreement(reason, record_ref, a_rows, b_entries):
    return {
        "reason": reason,
        "record_ref": record_ref,
        "a_location_ids": [r["location_id"] for r in a_rows],
        "b_location_ids": [e["location_id"] for e in b_entries],
        "system_a_values": [r["total_value_raw"] for r in a_rows],
        "system_b_values": [e["value_raw"] for e in b_entries],
        "entry_ids": [e["entry_id"] for e in b_entries],
    }


def find_disagreements(system_a_rows, system_b_rows):
    """
    system_a_rows: dicts with record_id, location_id, total_value, total_value_raw, state
    system_b_rows: dicts with entry_id, record_ref_raw, location_id, value, value_raw

    Returns a list of disagreement dicts:
        reason, record_ref, a_location_ids, b_location_ids,
        system_a_values, system_b_values, entry_ids

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
                _disagreement(ORPHAN_REF, entry["record_ref_raw"], [], [entry])
            )

    for key, a_rows in a_by_ref.items():
        entries = b_by_ref.get(key, [])
        record_ref = a_rows[0]["record_id"]

        # Two System A records claiming one reference: there is no single row left to
        # compare against, so report the ambiguity itself and stop there.
        if len(a_rows) > 1:
            disagreements.append(
                _disagreement(DUPLICATE_IN_A, record_ref, a_rows, entries)
            )
            continue

        a_row = a_rows[0]
        voided = (a_row.get("state") or "").strip().upper() == VOIDED

        if not entries:
            # A voided record having no entry in System B is the expected outcome,
            # not a disagreement.
            if not voided:
                disagreements.append(
                    _disagreement(MISSING_IN_B, record_ref, [a_row], [])
                )
            continue

        if voided:
            disagreements.append(
                _disagreement(VOIDED_IN_A, record_ref, [a_row], entries)
            )
            continue

        if len(entries) > 1:
            if not _is_split(a_row, entries):
                disagreements.append(
                    _disagreement(DUPLICATE_IN_B, record_ref, [a_row], entries)
                )
                continue
            # A proven split already reconciles against System A's total, so fall
            # through to the location check below.
        elif not _values_agree(a_row["total_value"], entries[0]["value"]):
            disagreements.append(
                _disagreement(VALUE_MISMATCH, record_ref, [a_row], entries)
            )
            continue

        # The values reconcile, but the two systems may still have filed the record
        # under different locations - and therefore, possibly, different tenants.
        if any(e["location_id"] != a_row["location_id"] for e in entries):
            disagreements.append(
                _disagreement(LOCATION_MISMATCH, record_ref, [a_row], entries)
            )

    return disagreements
