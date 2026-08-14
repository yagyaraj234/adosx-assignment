from app.compare import (
    DUPLICATE_IN_B,
    MISSING_IN_B,
    ORPHAN_REF,
    VALUE_MISMATCH,
    find_disagreements,
)


def a_row(record_id="REC-1001", location_id="LOC-101", total_value=100.0, raw="100.00"):
    return {
        "record_id": record_id,
        "location_id": location_id,
        "total_value": total_value,
        "total_value_raw": raw,
    }


def b_row(entry_id="ENT-1", record_ref_raw="REC-1001", location_id="LOC-101", value=100.0, raw="100.00"):
    return {
        "entry_id": entry_id,
        "record_ref_raw": record_ref_raw,
        "location_id": location_id,
        "value": value,
        "value_raw": raw,
    }


def test_agreeing_records_produce_no_disagreement():
    result = find_disagreements([a_row()], [b_row()])
    assert result == []


def test_record_missing_from_system_b():
    result = find_disagreements([a_row()], [])
    assert len(result) == 1
    assert result[0]["reason"] == MISSING_IN_B
    assert result[0]["record_ref"] == "REC-1001"


def test_entry_pointing_at_nonexistent_record_is_orphan():
    result = find_disagreements([], [b_row(record_ref_raw="REC-9999")])
    assert len(result) == 1
    assert result[0]["reason"] == ORPHAN_REF


def test_same_record_entered_twice_is_flagged_once_with_both_values():
    entries = [b_row(entry_id="ENT-1", raw="100.00"), b_row(entry_id="ENT-2", raw="105.00")]
    result = find_disagreements([a_row()], entries)
    assert len(result) == 1
    assert result[0]["reason"] == DUPLICATE_IN_B
    assert result[0]["system_b_value"] == "100.00; 105.00"
    assert set(result[0]["entry_ids"]) == {"ENT-1", "ENT-2"}


def test_different_values_for_same_record_flagged():
    result = find_disagreements([a_row(total_value=100.0)], [b_row(value=150.0, raw="150.00")])
    assert len(result) == 1
    assert result[0]["reason"] == VALUE_MISMATCH


def test_value_within_tolerance_is_not_flagged():
    result = find_disagreements(
        [a_row(total_value=100.00, raw="100.00")], [b_row(value=100.004, raw="100.004")]
    )
    assert result == []


def test_unparseable_value_disagrees_with_a_real_number():
    result = find_disagreements([a_row(total_value=100.0)], [b_row(value=None, raw="")])
    assert len(result) == 1
    assert result[0]["reason"] == VALUE_MISMATCH


def test_ref_normalization_matches_dirty_variants():
    result = find_disagreements([a_row(record_id="REC-1034")], [b_row(record_ref_raw="rec1034")])
    assert result == []
