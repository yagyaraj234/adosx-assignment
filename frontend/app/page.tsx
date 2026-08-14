"use client";

import { useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Disagreement = {
  reason: string;
  record_ref: string;
  location_id: string;
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

export default function Home() {
  const [orgs, setOrgs] = useState<string[]>([]);
  const [orgId, setOrgId] = useState("");
  const [reason, setReason] = useState("");
  const [sort, setSort] = useState<"value" | "-value">("value");
  const [rows, setRows] = useState<Disagreement[]>([]);
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
    fetch(`${API_BASE}/api/disagreements?${params}`)
      .then((r) => r.json())
      .then(setRows)
      .catch(() => setError("Could not reach the API. Is the backend running on :8000?"));
  }, [orgId, reason, sort]);

  return (
    <main style={{ fontFamily: "sans-serif", padding: "2rem", maxWidth: 900 }}>
      <h1>Disagreements</h1>

      {error && <p style={{ color: "red" }}>{error}</p>}

      <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem" }}>
        <label>
          Org (tenant):{" "}
          <select value={orgId} onChange={(e) => setOrgId(e.target.value)}>
            {orgs.map((o) => (
              <option key={o} value={o}>
                {o}
              </option>
            ))}
          </select>
        </label>

        <label>
          Reason:{" "}
          <select value={reason} onChange={(e) => setReason(e.target.value)}>
            {REASONS.map((r) => (
              <option key={r.value} value={r.value}>
                {r.label}
              </option>
            ))}
          </select>
        </label>

        <label>
          Sort by value:{" "}
          <select value={sort} onChange={(e) => setSort(e.target.value as "value" | "-value")}>
            <option value="value">Ascending</option>
            <option value="-value">Descending</option>
          </select>
        </label>
      </div>

      <table border={1} cellPadding={6} style={{ borderCollapse: "collapse", width: "100%" }}>
        <thead>
          <tr>
            <th>Reason</th>
            <th>Record</th>
            <th>Location</th>
            <th>System A value</th>
            <th>System B value</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={`${row.reason}-${row.record_ref}-${row.entry_ids.join(",")}`}>
              <td>{row.reason}</td>
              <td>{row.record_ref}</td>
              <td>{row.location_id}</td>
              <td>{row.system_a_value ?? "(none)"}</td>
              <td>{row.system_b_value ?? "(none)"}</td>
            </tr>
          ))}
          {rows.length === 0 && (
            <tr>
              <td colSpan={5}>No disagreements for this org/filter.</td>
            </tr>
          )}
        </tbody>
      </table>
    </main>
  );
}
