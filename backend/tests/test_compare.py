from app.compare import (
    DUPLICATE_IN_A,
    DUPLICATE_IN_B,
    LOCATION_MISMATCH,
    MISSING_IN_B,
    ORPHAN_REF,
    VALUE_MISMATCH,
    VOIDED_IN_A,
    find_disagreements,
)


def a_row(
    record_id="REC-1001",
    location_id="LOC-101",
    total_value=100.0,
    raw="100.00",
    state="CONFIRMED",
):
    return {
        "record_id": record_id,
        "location_id": location_id,
        "total_value": total_value,
        "total_value_raw": raw,
        "state": state,
    }


def b_row(entry_id="ENT-1", record_ref_raw="REC-1001", location_id="LOC-101", value=100.0, raw="100.00"):
    return {
        "entry_id": entry_id,
        "record_ref_raw": record_ref_raw,
        "location_id": location_id,
        "value": value,
        "value_raw": raw,
    }


def only(result):
    assert len(result) == 1, result
    return result[0]


def test_agreeing_records_produce_no_disagreement():
    assert find_disagreements([a_row()], [b_row()]) == []


# --- the four reasons the brief asks for ------------------------------------------


def test_record_missing_from_system_b():
    found = only(find_disagreements([a_row()], []))
    assert found["reason"] == MISSING_IN_B
    assert found["record_ref"] == "REC-1001"
    assert found["system_b_values"] == []


def test_entry_pointing_at_nonexistent_record_is_orphan():
    found = only(find_disagreements([], [b_row(record_ref_raw="REC-9999")]))
    assert found["reason"] == ORPHAN_REF
    assert found["system_a_values"] == []


def test_same_record_entered_twice_is_flagged_once_with_both_values():
    entries = [b_row(entry_id="ENT-1", raw="100.00"), b_row(entry_id="ENT-2", raw="100.00")]
    found = only(find_disagreements([a_row()], entries))
    assert found["reason"] == DUPLICATE_IN_B
    assert found["system_b_values"] == ["100.00", "100.00"]
    assert set(found["entry_ids"]) == {"ENT-1", "ENT-2"}


def test_different_values_for_same_record_flagged():
    found = only(find_disagreements([a_row(total_value=100.0)], [b_row(value=150.0, raw="150.00")]))
    assert found["reason"] == VALUE_MISMATCH


# --- the three extra reasons ------------------------------------------------------


def test_two_system_a_records_claiming_one_reference_is_flagged():
    rows = [a_row(record_id="REC-1034"), a_row(record_id="rec1034", raw="105.00")]
    found = only(find_disagreements(rows, []))
    assert found["reason"] == DUPLICATE_IN_A
    assert found["system_a_values"] == ["100.00", "105.00"]


def test_matching_values_filed_under_different_locations_is_flagged():
    found = only(find_disagreements([a_row(location_id="LOC-102")], [b_row(location_id="LOC-201")]))
    assert found["reason"] == LOCATION_MISMATCH
    assert found["a_location_ids"] == ["LOC-102"]
    assert found["b_location_ids"] == ["LOC-201"]  # the API decides who may see which


def test_voided_record_still_present_in_system_b_is_flagged():
    found = only(find_disagreements([a_row(state="VOIDED")], [b_row()]))
    assert found["reason"] == VOIDED_IN_A


# --- non-errors: things that look wrong and are not --------------------------------


def test_entries_summing_to_the_system_a_total_are_a_split_not_a_duplicate():
    entries = [
        b_row(entry_id="ENT-1", value=40.0, raw="40.00"),
        b_row(entry_id="ENT-2", value=60.0, raw="60.00"),
    ]
    assert find_disagreements([a_row(total_value=100.0)], entries) == []


def test_split_entries_that_do_not_add_up_are_still_a_duplicate():
    entries = [
        b_row(entry_id="ENT-1", value=40.0, raw="40.00"),
        b_row(entry_id="ENT-2", value=70.0, raw="70.00"),
    ]
    assert only(find_disagreements([a_row(total_value=100.0)], entries))["reason"] == DUPLICATE_IN_B


def test_split_cannot_be_proven_when_a_value_is_unparseable():
    entries = [
        b_row(entry_id="ENT-1", value=40.0, raw="40.00"),
        b_row(entry_id="ENT-2", value=None, raw=""),
    ]
    assert only(find_disagreements([a_row(total_value=100.0)], entries))["reason"] == DUPLICATE_IN_B


def test_voided_record_absent_from_system_b_is_not_a_disagreement():
    assert find_disagreements([a_row(state="VOIDED")], []) == []


def test_value_within_tolerance_is_not_flagged():
    result = find_disagreements(
        [a_row(total_value=100.00, raw="100.00")], [b_row(value=100.004, raw="100.004")]
    )
    assert result == []


# --- dirty references --------------------------------------------------------------


def test_unparseable_value_disagrees_with_a_real_number():
    found = only(find_disagreements([a_row(total_value=100.0)], [b_row(value=None, raw="")]))
    assert found["reason"] == VALUE_MISMATCH


def test_ref_normalization_matches_dirty_variants():
    assert find_disagreements([a_row(record_id="REC-1034")], [b_row(record_ref_raw="rec1034")]) == []


def test_ref_normalization_matches_spaced_variant():
    assert find_disagreements([a_row(record_id="REC-1070")], [b_row(record_ref_raw=" REC - 1070 ")]) == []


def test_ref_normalization_matches_bare_digit_variant():
    assert find_disagreements([a_row(record_id="REC-1112")], [b_row(record_ref_raw="1112")]) == []


def test_unnormalizable_refs_do_not_collapse_into_one_bucket():
    """Two references that will not normalize are two orphans, not one duplicate."""
    entries = [
        b_row(entry_id="ENT-1", record_ref_raw="???"),
        b_row(entry_id="ENT-2", record_ref_raw="n/a"),
    ]
    result = find_disagreements([], entries)
    assert [d["reason"] for d in result] == [ORPHAN_REF, ORPHAN_REF]


def test_blank_references_never_match_each_other():
    """A blank record_id and a blank record_ref are not evidence of the same record."""
    result = find_disagreements([a_row(record_id="")], [b_row(record_ref_raw="")])
    assert sorted(d["reason"] for d in result) == [MISSING_IN_B, ORPHAN_REF]
