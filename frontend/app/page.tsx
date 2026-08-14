"use client";

import { useEffect, useState } from "react";
import styles from "./page.module.css";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Disagreement = {
  reason: string;
  record_ref: string;
  location_id: string;
  location_name: string | null;
  system_a_value: string | null;
  system_b_value: string | null;
  entry_ids: string[];
  sort_value: number | null;
};

const REASONS = [
  { value: "", label: "All reasons" },
  { value: "missing_in_b", label: "Missing in System B" },
  { value: "orphan_ref", label: "Orphan ref in System B" },
  { value: "duplicate_in_b", label: "Duplicate in System B" },
  { value: "value_mismatch", label: "Value mismatch" },
];

const REASON_LABEL: Record<string, string> = Object.fromEntries(
  REASONS.filter((r) => r.value).map((r) => [r.value, r.label])
);

export default function Home() {
  const [orgs, setOrgs] = useState<string[]>([]);
  const [orgId, setOrgId] = useState("");
  const [reason, setReason] = useState("");
  const [sort, setSort] = useState<"value" | "-value">("value");
  const [rows, setRows] = useState<Disagreement[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/orgs`)
      .then((r) => r.json())
      .then((data: string[]) => {
        setOrgs(data);
        if (data.length > 0) setOrgId(data[0]);
      })
      .catch(() => setError("Could not reach the API. Is the backend running on :8000?"));
  }, []);

  useEffect(() => {
    if (!orgId) return;
    const params = new URLSearchParams({ org_id: orgId, sort });
    if (reason) params.set("reason", reason);
    setRows(null);
    fetch(`${API_BASE}/api/disagreements?${params}`)
      .then((r) => r.json())
      .then(setRows)
      .catch(() => setError("Could not reach the API. Is the backend running on :8000?"));
  }, [orgId, reason, sort]);

  return (
    <main className={styles.page}>
      <div className={styles.header}>
        <h1>Disagreements</h1>
        <p className={styles.subtitle}>
          Records where System A and System B disagree, scoped to one tenant at a time.
        </p>
      </div>

      {error && <div className={`${styles.banner} ${styles.error}`}>{error}</div>}

      <div className={styles.toolbar}>
        <label className={styles.field}>
          Org (tenant)
          <select value={orgId} onChange={(e) => setOrgId(e.target.value)}>
            {orgs.map((o) => (
              <option key={o} value={o}>
                {o}
              </option>
            ))}
          </select>
        </label>

        <label className={styles.field}>
          Reason
          <select value={reason} onChange={(e) => setReason(e.target.value)}>
            {REASONS.map((r) => (
              <option key={r.value} value={r.value}>
                {r.label}
              </option>
            ))}
          </select>
        </label>

        <label className={styles.field}>
          Sort by value
          <select value={sort} onChange={(e) => setSort(e.target.value as "value" | "-value")}>
            <option value="value">Ascending</option>
            <option value="-value">Descending</option>
          </select>
        </label>
      </div>

      <p className={styles.summary}>
        {rows === null ? "Loading…" : `${rows.length} disagreement${rows.length === 1 ? "" : "s"}`}
      </p>

      <div className={styles.tableWrap}>
        <table>
          <thead>
            <tr>
              <th>Reason</th>
              <th>Record</th>
              <th>Location</th>
              <th className={styles.value}>System A value</th>
              <th className={styles.value}>System B value</th>
            </tr>
          </thead>
          <tbody>
            {rows &&
              rows.map((row) => (
                <tr key={`${row.reason}-${row.record_ref}-${row.entry_ids.join(",")}`}>
                  <td>
                    <span className={`${styles.badge} ${styles[row.reason] ?? ""}`}>
                      {REASON_LABEL[row.reason] ?? row.reason}
                    </span>
                  </td>
                  <td>{row.record_ref}</td>
                  <td>
                    {row.location_name ?? row.location_id}
                    {row.location_name && (
                      <span className={styles.muted}> ({row.location_id})</span>
                    )}
                  </td>
                  <td className={styles.value}>{row.system_a_value ?? "—"}</td>
                  <td className={styles.value}>{row.system_b_value ?? "—"}</td>
                </tr>
              ))}
          </tbody>
        </table>
        {rows && rows.length === 0 && (
          <div className={styles.empty}>No disagreements for this org/filter.</div>
        )}
      </div>
    </main>
  );
}
