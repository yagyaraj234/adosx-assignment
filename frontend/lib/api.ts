import { Reason, ReasonFilter } from "./reasons";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Disagreement = {
  reason: Reason;
  record_ref: string;
  /** System A's location, or null when it belongs to another tenant (redacted server-side). */
  location_id: string | null;
  location_name: string | null;
  /** System B's location, under the same redaction rule. */
  b_location_id: string | null;
  b_location_name: string | null;
  /** The other system filed this record under a tenant that is not the one being viewed. */
  cross_tenant: boolean;
  system_a_values: string[];
  system_b_values: string[];
  entry_ids: string[];
  sort_value: number | null;
};

export type SortOrder = "value" | "-value";

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

export function fetchOrgs(): Promise<string[]> {
  return getJson(`${API_BASE}/api/orgs`);
}

export function fetchDisagreements(params: {
  orgId: string;
  reason: ReasonFilter;
  sort: SortOrder;
}): Promise<Disagreement[]> {
  const query = new URLSearchParams({ org_id: params.orgId, sort: params.sort });
  if (params.reason) query.set("reason", params.reason);
  return getJson(`${API_BASE}/api/disagreements?${query}`);
}
