from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from app.compare import find_disagreements
from app.db import engine, reset_db
from app.importer import import_data
from app.models import Location, SystemARecord, SystemBEntry
from app.parsing import parse_number

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


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


def _first_value(raw: str | None) -> float | None:
    if raw is None:
        return None
    return parse_number(raw.split(";")[0])


UNRESOLVED_ORG = "UNRESOLVED"  # bucket for a location_id that isn't in locations.csv at all


def _location_maps(locations):
    org_of = {loc.location_id: loc.org_id for loc in locations}
    name_of = {loc.location_id: loc.location_name for loc in locations}
    return org_of, name_of


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

    disagreements = find_disagreements(a_rows, b_rows)

    scoped = [
        d
        for d in disagreements
        if org_of.get(d["location_id"], UNRESOLVED_ORG) == org_id
    ]

    if reason:
        scoped = [d for d in scoped if d["reason"] == reason]

    reverse = sort.startswith("-")
    for d in scoped:
        a_val = _first_value(d["system_a_value"])
        b_val = _first_value(d["system_b_value"])
        d["sort_value"] = a_val if a_val is not None else b_val
        d["location_name"] = name_of.get(d["location_id"])

    def sort_key(d):
        v = d["sort_value"]
        if v is None:
            return (1, 0)
        return (0, -v if reverse else v)

    scoped.sort(key=sort_key)

    return scoped
