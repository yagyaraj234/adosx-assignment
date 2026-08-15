import { Reason, ReasonFilter } from "./reasons";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Disagreement = {
  reason: Reason;
  record_ref: string;
  location_id: string;
  location_name: string | null;
  system_a_value: string | null;
  system_b_value: string | null;
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
