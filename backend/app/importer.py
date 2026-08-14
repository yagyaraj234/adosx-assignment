import csv
from pathlib import Path

from sqlmodel import Session

from app.models import Location, SystemARecord, SystemBEntry
from app.parsing import normalize_ref, parse_number


def _read_rows(path: Path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def import_data(session: Session, data_dir: Path):
    """Load all three CSVs. Every row is kept - dirty values become None, never a dropped row."""
    for row in _read_rows(data_dir / "locations.csv"):
        session.add(
            Location(
                location_id=row["location_id"],
                org_id=row["org_id"],
                location_name=row["location_name"],
            )
        )

    for row in _read_rows(data_dir / "system_a.csv"):
        session.add(
            SystemARecord(
                record_id=row["record_id"],
                location_id=row["location_id"],
                event_date=row["event_date"],
                category_code=row["category_code"],
                actor_id=row["actor_id"],
                base_value_raw=row["base_value"],
                adjustment_raw=row["adjustment"],
                total_value_raw=row["total_value"],
                total_value=parse_number(row["total_value"]),
                state=row["state"],
            )
        )

    for row in _read_rows(data_dir / "system_b.csv"):
        session.add(
            SystemBEntry(
                entry_id=row["entry_id"],
                record_ref_raw=row["record_ref"],
                record_ref_normalized=normalize_ref(row["record_ref"]),
                location_id=row["location_id"],
                recorded_on=row["recorded_on"],
                value_raw=row["value"],
                value=parse_number(row["value"]),
                label=row["label"],
            )
        )

    session.commit()
