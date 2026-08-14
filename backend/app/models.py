from typing import Optional

from sqlmodel import Field, SQLModel


class Location(SQLModel, table=True):
    location_id: str = Field(primary_key=True)
    org_id: str
    location_name: str


class SystemARecord(SQLModel, table=True):
    """One row per event as System A recorded it. record_id is the identifier."""

    record_id: str = Field(primary_key=True)
    location_id: str
    event_date: str
    category_code: str
    actor_id: str
    base_value_raw: str
    adjustment_raw: str
    total_value_raw: str
    total_value: Optional[float]
    state: str


class SystemBEntry(SQLModel, table=True):
    """One row per entry as System B recorded it. record_ref may be dirty or dangling."""

    entry_id: str = Field(primary_key=True)
    record_ref_raw: str
    record_ref_normalized: Optional[str]
    location_id: str
    recorded_on: str
    value_raw: str
    value: Optional[float]
    label: str
