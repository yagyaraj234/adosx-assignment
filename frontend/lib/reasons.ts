export type Reason =
  | "missing_in_b"
  | "orphan_ref"
  | "duplicate_in_b"
  | "duplicate_in_a"
  | "value_mismatch"
  | "location_mismatch"
  | "voided_in_a";

export type ReasonFilter = Reason | "";

export const REASON_LABEL: Record<Reason, string> = {
  missing_in_b: "Missing in System B",
  orphan_ref: "Orphan ref in System B",
  duplicate_in_b: "Duplicate in System B",
  duplicate_in_a: "Duplicate in System A",
  value_mismatch: "Value mismatch",
  location_mismatch: "Location mismatch",
  voided_in_a: "Voided in System A",
};

export const REASON_DESCRIPTION: Record<Reason, string> = {
  missing_in_b: "Record exists in System A but has no matching entry in System B.",
  orphan_ref: "System B has an entry referencing this record, but System A has no such record.",
  duplicate_in_b:
    "System B has more than one entry for this record and they do not add up to System A's total. All values are shown, one per line.",
  duplicate_in_a: "Two System A records normalize to the same reference, so there is no single row to compare against.",
  value_mismatch: "Both systems have this record, but their values differ by more than a rounding tolerance.",
  location_mismatch:
    "The values agree, but the two systems filed this record under different locations — possibly different tenants.",
  voided_in_a: "System A voided this record, but System B still has an entry for it.",
};

export const REASONS: { value: ReasonFilter; label: string }[] = [
  { value: "", label: "All reasons" },
  ...(Object.keys(REASON_LABEL) as Reason[]).map((value) => ({ value, label: REASON_LABEL[value] })),
];
