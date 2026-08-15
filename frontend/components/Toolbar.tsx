import styles from "./Toolbar.module.css";
import { REASONS, ReasonFilter } from "@/lib/reasons";
import { SortOrder } from "@/lib/api";

export function Toolbar({
  orgs,
  orgId,
  onOrgChange,
  reason,
  onReasonChange,
  sort,
  onSortChange,
  disabled = false,
}: {
  orgs: string[];
  orgId: string;
  onOrgChange: (value: string) => void;
  reason: ReasonFilter;
  onReasonChange: (value: ReasonFilter) => void;
  sort: SortOrder;
  onSortChange: (value: SortOrder) => void;
  disabled?: boolean;
}) {
  return (
    <div className={styles.toolbar}>
      <label className={styles.field}>
        Org (tenant)
        <select value={orgId} disabled={disabled} onChange={(e) => onOrgChange(e.target.value)}>
          {orgs.map((o) => (
            <option key={o} value={o}>
              {o}
            </option>
          ))}
        </select>
      </label>

      <label className={styles.field}>
        Reason
        <select
          value={reason}
          disabled={disabled}
          onChange={(e) => onReasonChange(e.target.value as ReasonFilter)}
        >
          {REASONS.map((r) => (
            <option key={r.value} value={r.value}>
              {r.label}
            </option>
          ))}
        </select>
      </label>

      <label className={styles.field}>
        Sort by value
        <select value={sort} disabled={disabled} onChange={(e) => onSortChange(e.target.value as SortOrder)}>
          <option value="value">Ascending</option>
          <option value="-value">Descending</option>
        </select>
      </label>
    </div>
  );
}
