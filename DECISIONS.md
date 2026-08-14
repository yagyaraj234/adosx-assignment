# Decisions

1. **Stack: FastAPI + Next.js, not Django + React.** Rejected Django because the brief
   explicitly allows "if you are strong elsewhere, use it" — FastAPI + SQLModel gives the
   same batteries (validation, ORM, auto docs) with less framework ceremony for a
   single-endpoint API.

2. **SQLite, not Postgres.** Rejected Postgres/docker-compose because the brief explicitly
   says performance and infra aren't graded — SQLite needs zero setup and survives a clean
   clone, which is graded.

3. **SQLModel with tables recreated on every startup, no Alembic migrations.** Rejected a
   migrations tool because the schema never changes after this submission and the dataset
   is a static 120-row CSV re-imported fresh each run — migration tooling would be
   ceremony with no payoff.

4. **`record_ref` normalization is aggressive (case, dash, and prefix insensitive), not
   strict pattern matching.** Rejected requiring an exact `REC-####` shape after finding
   the data contains a bare-digit variant (`"1112"` for `REC-1112`) in addition to the
   case/dash variants — under-matching (missing a real match) is worse than over-matching
   for a brief whose whole point is finding true disagreements.

5. **Duplicate System B entries collapse into one disagreement row per `record_ref`,
   not one row per extra entry.** Rejected per-entry rows because the table is meant to
   be scanned by a human; grouping all versions of one duplicated record together (with
   both/all values shown) is what a reviewer actually needs to compare.

6. **Value comparison uses a 0.01 epsilon, not exact equality.** Rejected exact float
   equality because these are money values passed through CSV round-tripping — exact
   comparison risks flagging harmless rounding noise as a disagreement.

7. **No 5th "location mismatch" disagreement category**, even though System B carries its
   own `location_id` that could theoretically disagree with System A's. Rejected adding it
   because the brief asks for exactly four reasons — an unrequested category spends the
   day's time budget without adding scoring credit, and I noted the trade-off instead of
   silently building it.

8. **Tenant isolation is a required `org_id` query parameter resolved server-side through
   the `locations` join, not a login/session.** Rejected building fake auth because the
   brief explicitly says skip it — but the boundary itself ("must never leak across
   tenant") is still real: the API refuses to return rows outside the requested org, and
   the org is never inferred from anything the client claims about itself.

9. **The comparison function takes and returns plain dicts, with zero DB/ORM
   dependency.** Rejected writing it against SQLModel row objects because the brief singles
   out testing "the part where disagreements are decided" — a pure function over plain
   data is trivial to unit test without a database, a fixture, or a running app.

10. **Dirty data is absorbed by fallback values, not by inventing new categories.**
    Unparseable/blank values are stored as `None` (raw string kept for display), which the
    comparison naturally reports as `value_mismatch` against a real number — no separate
    "unparseable value" reason needed. Symmetrically, a disagreement whose `location_id`
    isn't in `locations.csv` falls into a synthetic `UNRESOLVED` org bucket rather than a
    `None` org that no tenant filter would ever match. Rejected inventing dedicated
    categories/handling for either case because both are really the same problem —
    "don't silently drop or hide a row" — solved once by falling back to a value the
    existing logic already knows how to handle, instead of twice by special-casing.
