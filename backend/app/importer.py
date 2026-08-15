import csv
from pathlib import Path

from sqlmodel import Session

from app.models import Location, SystemARecord, SystemBEntry
from app.parsing import normalize_ref, parse_number


def _read_rows(path: Path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _text(row, key):
    """A missing column or a short row becomes an empty string, never a KeyError."""
    return row.get(key) or ""


def _location(row):
    return Location(
        location_id=_text(row, "location_id"),
        org_id=_text(row, "org_id"),
        location_name=_text(row, "location_name"),
    )


def _a_record(row):
    return SystemARecord(
        record_id=_text(row, "record_id"),
        location_id=_text(row, "location_id"),
        event_date=_text(row, "event_date"),
        category_code=_text(row, "category_code"),
        actor_id=_text(row, "actor_id"),
        base_value_raw=_text(row, "base_value"),
        adjustment_raw=_text(row, "adjustment"),
        total_value_raw=_text(row, "total_value"),
        total_value=parse_number(_text(row, "total_value")),
        state=_text(row, "state"),
    )


def _b_entry(row):
    return SystemBEntry(
        entry_id=_text(row, "entry_id"),
        record_ref_raw=_text(row, "record_ref"),
        record_ref_normalized=normalize_ref(_text(row, "record_ref")),
        location_id=_text(row, "location_id"),
        recorded_on=_text(row, "recorded_on"),
        value_raw=_text(row, "value"),
        value=parse_number(_text(row, "value")),
        label=_text(row, "label"),
    )


FILES = (
    ("locations.csv", _location),
    ("system_a.csv", _a_record),
    ("system_b.csv", _b_entry),
)


def import_data(session: Session, data_dir: Path) -> list[str]:
    """Load all three CSVs and return one line per row the database refused.

    Dirty values become None with the raw string kept alongside, so no row is lost to
    an unparseable number. Each row is inserted on its own savepoint, so a row that is
    genuinely impossible to store (a duplicate primary key, say) is rejected on its own
    and reported to the caller instead of taking the other 300-odd rows down with it.
    """
    rejected: list[str] = []

    for filename, build in FILES:
        for line_no, row in enumerate(_read_rows(data_dir / filename), start=2):
            try:
                with session.begin_nested():
                    session.add(build(row))
            except Exception as exc:  # noqa: BLE001 - any failure must be reported, not raised
                reason = f"{type(exc).__name__}: {exc}".splitlines()[0]
                rejected.append(f"{filename} line {line_no}: {reason}")

    session.commit()
    return rejected
