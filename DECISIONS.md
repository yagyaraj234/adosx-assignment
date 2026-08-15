# Decisions

1. **Stack: FastAPI + Next.js, not Django + React.** Rejected Django because the brief
   explicitly allows "if you are strong elsewhere, use it" — FastAPI + SQLModel gives the
   same batteries (validation, ORM, auto docs) with less framework ceremony for a
   two-endpoint API.

2. **SQLite with tables dropped and recreated on every startup, no migration tool.**
   Rejected Postgres/docker-compose and Alembic because the dataset is a static 120-row
   CSV re-imported fresh each run and the schema never changes after this submission —
   both would be setup cost against a "runs from a clean clone" criterion, not for it.

3. **`record_ref` matching is aggressive (case-, dash-, space- and prefix-insensitive),
   and a reference that will not normalize gets a key of its own rather than a shared
   `None`.** Rejected strict `REC-####` matching after finding `rec1034`, `" REC - 1070 "`
   and a bare `1112` in the data; rejected the shared-`None` fallback because it makes
   every unparseable reference look like a match for every other one — a silent
   misclassification inside the one function whose job is to not lose rows.

4. **Several System B entries whose values *sum* to System A's total are a split, not a
   duplicate — decided on the arithmetic, not on the label.** `REC-1055`'s two entries
   (71950.93 + 107926.39) hit A's 179877.32 exactly, and one is labelled "Entry part 2 of
   2"; `REC-1042`'s two entries repeat the same 112837.06 and are a real double entry.
   Rejected parsing the label because it is free text, and rejected treating every
   multi-entry record as a duplicate because the brief states outright that "there may be
   more than one entry per record". If any value is unparseable the split cannot be
   proven, so the record falls back to `duplicate_in_b`.

5. **A `VOIDED` System A record is expected to be absent from System B: absent is a
   non-error, still present is `voided_in_a`.** Rejected ignoring `state` (the reading the
   first pass shipped — it made `REC-1019`, the single voided row in the data, invisible)
   and rejected the opposite reading, that a voided record with a matching value is simply
   another non-error, because then the two systems disagree about whether the event
   happened at all and nobody is told.

6. **`location_mismatch` is a fifth reason, and it is shown to *both* tenants with the
   other side's location redacted.** `REC-1077` is filed under `LOC-102` (ORG-A) by System
   A and `LOC-201` (ORG-B) by System B, with identical values — so under a four-reason
   comparison it disagrees about nothing and is invisible to everyone. The brief says
   "at minimum, catch these", so four is a floor. Rejected showing it to System A's org
   only (ORG-B never learns its own location is contested) and rejected hiding it from
   both (the bug being fixed). Ownership of that row is precisely what is unknown, so
   both tenants see the row and the disputed value — that value is the entire content of
   the disagreement, and hiding it leaves a row that says nothing. Everything that
   *identifies* the counterparty is withheld: its `location_id`, its location name, and
   the System B `entry_id`, which is filed under the other tenant's location and is
   dropped alongside it. The row says only "another tenant".

7. **A disagreement is visible to a tenant if *any* location it touches belongs to that
   tenant, and every location is redacted through one helper.** Rejected scoping by
   System A's `location_id` alone — that quietly assumes the two systems agree about
   ownership, which is the exact assumption `REC-1077` breaks. A `location_id` absent
   from `locations.csv` falls into a synthetic `UNRESOLVED` org rather than a `None` org
   no filter would ever match, so an unmapped row is still reachable by somebody.

8. **The importer inserts each row on its own savepoint and returns a list of the rows
   the database refused; missing columns and short rows become empty strings.** Rejected
   the single bulk `commit()` the first version used: one duplicate identifier or one
   truncated line raised `IntegrityError` and took all 361 rows down with it, which is
   the loudest possible way to fail the "nothing is silently dropped" requirement.
   Rejected surrogate primary keys as the fix — it would have made three tables' keys
   meaningless to remove a failure mode the report already covers.

9. **The comparison function takes and returns plain dicts, with zero DB/ORM
   dependency, and never filters by org.** Rejected writing it against SQLModel rows
   because the brief singles out testing "the part where disagreements are decided" — a
   pure function over plain data needs no database, fixture, or running app. Tenancy is
   deliberately left to the API: a disagreement can straddle two orgs, so the comparison
   is not the layer that can decide who sees it.

10. **Value comparison uses a 0.01 epsilon, not exact equality, and duplicates collapse
    into one row per record with every value listed.** Rejected exact float equality
    because these are money values round-tripped through CSV; rejected one row per extra
    entry because a human scanning the table wants all versions of one record side by
    side.
