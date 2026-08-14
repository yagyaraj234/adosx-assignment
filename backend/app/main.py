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
        import_data(session, DATA_DIR)
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


@app.get("/api/orgs")
def list_orgs():
    with Session(engine) as session:
        orgs = session.exec(select(Location.org_id).distinct()).all()
    return sorted(orgs)


@app.get("/api/disagreements")
def list_disagreements(
    org_id: str = Query(..., description="Tenant to scope results to - required, never inferred"),
    reason: str | None = None,
    sort: str = Query("value", pattern="^-?value$"),
):
    with Session(engine) as session:
        locations = session.exec(select(Location)).all()
        if org_id not in {loc.org_id for loc in locations}:
            raise HTTPException(status_code=404, detail=f"unknown org_id '{org_id}'")
        location_org = {loc.location_id: loc.org_id for loc in locations}

        a_rows = [r.model_dump() for r in session.exec(select(SystemARecord)).all()]
        b_rows = [r.model_dump() for r in session.exec(select(SystemBEntry)).all()]

    disagreements = find_disagreements(a_rows, b_rows)

    scoped = [
        d for d in disagreements if location_org.get(d["location_id"]) == org_id
    ]

    if reason:
        scoped = [d for d in scoped if d["reason"] == reason]

    reverse = sort.startswith("-")
    for d in scoped:
        a_val = _first_value(d["system_a_value"])
        b_val = _first_value(d["system_b_value"])
        d["sort_value"] = a_val if a_val is not None else b_val

    def sort_key(d):
        v = d["sort_value"]
        if v is None:
            return (1, 0)
        return (0, -v if reverse else v)

    scoped.sort(key=sort_key)

    return scoped
