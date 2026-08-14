from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine, select

from app.importer import import_data
from app.models import Location, SystemARecord, SystemBEntry

LOCATIONS_CSV = "location_id,org_id,location_name\nLOC-1,ORG-A,Loc One\n"

SYSTEM_A_CSV = (
    "record_id,location_id,event_date,category_code,actor_id,base_value,adjustment,total_value,state\n"
    "REC-1,LOC-1,2026-01-01,CAT-01,USR-1,10.00,1.00,11.00,CONFIRMED\n"
    "REC-2,LOC-1,2026-01-02,CAT-01,USR-1,not-a-number,1.00,,CONFIRMED\n"
)

SYSTEM_B_CSV = (
    "entry_id,record_ref,location_id,recorded_on,value,label\n"
    "ENT-1,REC-1,LOC-1,2026-01-01,11.00,ok\n"
    "ENT-2,REC-999,LOC-1,2026-01-01,5.00,dangling ref\n"
    "ENT-3,rec1,LOC-1,2026-01-01,,blank value\n"
)


def _write_dataset(dir_path: Path):
    (dir_path / "locations.csv").write_text(LOCATIONS_CSV)
    (dir_path / "system_a.csv").write_text(SYSTEM_A_CSV)
    (dir_path / "system_b.csv").write_text(SYSTEM_B_CSV)


def test_importer_keeps_every_row_even_when_dirty(tmp_path):
    _write_dataset(tmp_path)

    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        import_data(session, tmp_path)

        assert len(session.exec(select(Location)).all()) == 1
        assert len(session.exec(select(SystemARecord)).all()) == 2
        assert len(session.exec(select(SystemBEntry)).all()) == 3

        blank_row = session.get(SystemARecord, "REC-2")
        assert blank_row.total_value is None  # unparseable, but the row itself survives
        assert blank_row.total_value_raw == ""

        blank_value_entry = session.get(SystemBEntry, "ENT-3")
        assert blank_value_entry.value is None
        assert blank_value_entry.record_ref_normalized == "REC-1"  # normalized despite no dash/case
