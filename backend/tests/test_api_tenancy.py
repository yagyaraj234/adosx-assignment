"""The tenant boundary, tested against the real CSVs through the real app.

The comparison logic is unit-tested in test_compare.py. This file covers the layer the
brief actually leads with: what a tenant is allowed to see. TestClient runs the app's
lifespan, so these hit the same import and the same 120 rows the running server does.
"""
import json

import pytest
from fastapi.testclient import TestClient

from app.main import app

ORG_LOCATIONS = {"ORG-A": {"LOC-101", "LOC-102", "LOC-103"}, "ORG-B": {"LOC-201", "LOC-202"}}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as running:
        yield running


def get(client, org_id, **params):
    response = client.get("/api/disagreements", params={"org_id": org_id, **params})
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.parametrize("org_id", sorted(ORG_LOCATIONS))
def test_no_other_tenants_location_appears_anywhere_in_the_response(client, org_id):
    """Not just in the location fields - nowhere in the payload at all."""
    body = json.dumps(get(client, org_id))
    for other_org, locations in ORG_LOCATIONS.items():
        if other_org == org_id:
            continue
        for location_id in locations:
            assert location_id not in body, f"{org_id} was shown {location_id}"


def test_a_record_each_system_filed_under_a_different_tenant_reaches_both(client):
    """REC-1077: System A says LOC-102 (ORG-A), System B says LOC-201 (ORG-B). Neither
    org may see the other's location, but neither may be left unaware of the row."""
    a_side = [d for d in get(client, "ORG-A") if d["record_ref"] == "REC-1077"]
    b_side = [d for d in get(client, "ORG-B") if d["record_ref"] == "REC-1077"]
    assert len(a_side) == 1 and len(b_side) == 1

    assert a_side[0]["location_id"] == "LOC-102"
    assert a_side[0]["b_location_id"] is None  # ORG-B's location, redacted
    assert b_side[0]["location_id"] is None  # ORG-A's location, redacted
    assert b_side[0]["b_location_id"] == "LOC-201"
    assert a_side[0]["cross_tenant"] and b_side[0]["cross_tenant"]

    # The System B entry belongs to ORG-B, so only ORG-B is given its id.
    assert a_side[0]["entry_ids"] == []
    assert b_side[0]["entry_ids"] == ["ENT/2026/4077"]


def test_every_row_a_tenant_sees_touches_one_of_its_own_locations(client):
    for org_id, own in ORG_LOCATIONS.items():
        for d in get(client, org_id):
            visible = {d["location_id"], d["b_location_id"]} - {None}
            assert visible and visible <= own, f"{org_id} got {visible} for {d['record_ref']}"


def test_unknown_org_is_an_error(client):
    assert client.get("/api/disagreements", params={"org_id": "ORG-Z"}).status_code == 404


def test_reason_filter_is_a_subset_of_the_unfiltered_result(client):
    everything = get(client, "ORG-A")
    filtered = get(client, "ORG-A", reason="value_mismatch")
    assert filtered == [d for d in everything if d["reason"] == "value_mismatch"]
    assert filtered  # the filter is actually exercised on this dataset


def test_sort_by_value_orders_both_directions_with_unparseable_values_last(client):
    def values(rows):
        return [d["sort_value"] for d in rows if d["sort_value"] is not None]

    ascending = get(client, "ORG-A", sort="value")
    descending = get(client, "ORG-A", sort="-value")
    assert values(ascending) == sorted(values(ascending))
    assert values(descending) == sorted(values(descending), reverse=True)
    assert [d["sort_value"] for d in ascending].count(None) == 0 or ascending[-1]["sort_value"] is None
