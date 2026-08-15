from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from app.compare import REASONS, find_disagreements
from app.db import engine, reset_db
from app.importer import import_data
from app.models import Location, SystemARecord, SystemBEntry
from app.parsing import parse_number

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

UNRESOLVED_ORG = "UNRESOLVED"  # bucket for a location_id that isn't in locations.csv at all


@asynccontextmanager
async def lifespan(app: FastAPI):
    reset_db()
    with Session(engine) as session:
        rejected = import_data(session, DATA_DIR)
    for line in rejected:
        print(f"[import] rejected {line}", flush=True)
    print(f"[import] {len(rejected)} row(s) rejected", flush=True)
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _location_maps(locations):
    org_of = {loc.location_id: loc.org_id for loc in locations}
    name_of = {loc.location_id: loc.location_name for loc in locations}
    return org_of, name_of


def _org_of(location_id, org_of):
    return org_of.get(location_id, UNRESOLVED_ORG)


def _own_location(location_ids, org_id, org_of):
    """The first location on one side of a disagreement that belongs to the requesting
    org, or None. Every redaction goes through here, so a location's name can never be
    returned without its id having passed the same check."""
    for location_id in location_ids:
        if _org_of(location_id, org_of) == org_id:
            return location_id
    return None


def _own_entry_ids(disagreement, org_id, org_of):
    """System B entry ids, minus any entry filed under another tenant's location.

    `entry_ids` and `b_location_ids` are built in step from the same entries, so an entry
    id can be matched to the location it was filed under and dropped with it.
    """
    return [
        entry_id
        for entry_id, location_id in zip(disagreement["entry_ids"], disagreement["b_location_ids"])
        if _org_of(location_id, org_of) == org_id
    ]


def _sort_value(disagreement):
    """Sort on System A's value when there is one, else System B's."""
    for raw in [*disagreement["system_a_values"], *disagreement["system_b_values"]]:
        value = parse_number(raw)
        if value is not None:
            return value
    return None


@app.get("/api/orgs")
def list_orgs():
    with Session(engine) as session:
        locations = session.exec(select(Location)).all()
        org_of, _ = _location_maps(locations)
        a_locs = session.exec(select(SystemARecord.location_id)).all()
        b_locs = session.exec(select(SystemBEntry.location_id)).all()

    orgs = {loc.org_id for loc in locations}
    if any(loc_id not in org_of for loc_id in [*a_locs, *b_locs]):
        orgs.add(UNRESOLVED_ORG)  # a row references a location that locations.csv never maps to an org

    return sorted(orgs)


@app.get("/api/disagreements")
def list_disagreements(
    org_id: str = Query(..., description="Tenant to scope results to - required, never inferred"),
    reason: str | None = None,
    sort: str = Query("value", pattern="^-?value$"),
):
    with Session(engine) as session:
        locations = session.exec(select(Location)).all()
        org_of, name_of = _location_maps(locations)

        a_rows = [r.model_dump() for r in session.exec(select(SystemARecord)).all()]
        b_rows = [r.model_dump() for r in session.exec(select(SystemBEntry)).all()]

    known_orgs = {loc.org_id for loc in locations} | {UNRESOLVED_ORG}
    if org_id not in known_orgs:
        raise HTTPException(status_code=404, detail=f"unknown org_id '{org_id}'")
    if reason and reason not in REASONS:
        # An unrecognised filter returns an error, not a silently empty table.
        raise HTTPException(status_code=400, detail=f"unknown reason '{reason}'")

    scoped = []
    for d in find_disagreements(a_rows, b_rows):
        # A disagreement is visible to a tenant if *any* location it touches belongs to
        # that tenant - otherwise a record the two systems filed under different orgs
        # would be invisible to both of them.
        involved_orgs = {
            _org_of(loc_id, org_of) for loc_id in [*d["a_location_ids"], *d["b_location_ids"]]
        }
        if org_id not in involved_orgs:
            continue
        if reason and d["reason"] != reason:
            continue

        a_location = _own_location(d["a_location_ids"], org_id, org_of)
        b_location = _own_location(d["b_location_ids"], org_id, org_of)
        scoped.append(
            {
                "reason": d["reason"],
                "record_ref": d["record_ref"],
                "location_id": a_location,
                "location_name": name_of.get(a_location) if a_location else None,
                "b_location_id": b_location,
                "b_location_name": name_of.get(b_location) if b_location else None,
                # True when the other system filed this record under a tenant that is
                # not this one. The other tenant's location is redacted above; only the
                # fact that it is elsewhere crosses the boundary.
                "cross_tenant": involved_orgs != {org_id},
                # Values cross the boundary on purpose (DECISIONS #6): the disputed value
                # is the whole point of the row. Identifiers do not.
                "system_a_values": d["system_a_values"],
                "system_b_values": d["system_b_values"],
                "entry_ids": _own_entry_ids(d, org_id, org_of),
                "sort_value": _sort_value(d),
            }
        )

    reverse = sort.startswith("-")

    def sort_key(d):
        value = d["sort_value"]
        if value is None:
            return (1, 0)  # rows with no parseable value on either side always sort last
        return (0, -value if reverse else value)

    scoped.sort(key=sort_key)

    return scoped
