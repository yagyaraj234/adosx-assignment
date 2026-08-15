export type Reason = "missing_in_b" | "orphan_ref" | "duplicate_in_b" | "value_mismatch";
export type ReasonFilter = Reason | "";

export const REASONS: { value: ReasonFilter; label: string }[] = [
  { value: "", label: "All reasons" },
  { value: "missing_in_b", label: "Missing in System B" },
  { value: "orphan_ref", label: "Orphan ref in System B" },
  { value: "duplicate_in_b", label: "Duplicate in System B" },
  { value: "value_mismatch", label: "Value mismatch" },
];

export const REASON_LABEL: Record<Reason, string> = {
  missing_in_b: "Missing in System B",
  orphan_ref: "Orphan ref in System B",
  duplicate_in_b: "Duplicate in System B",
  value_mismatch: "Value mismatch",
};

export const REASON_DESCRIPTION: Record<Reason, string> = {
  missing_in_b: "Record exists in System A but has no matching entry in System B.",
  orphan_ref: "System B has an entry referencing this record, but System A has no such record.",
  duplicate_in_b: "System B has more than one entry for this record. All of its values are shown, one per line.",
  value_mismatch: "Both systems have this record, but their values differ by more than a rounding tolerance.",
};
