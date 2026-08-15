import styles from './DisagreementsTable.module.css';
import { REASON_LABEL, REASON_DESCRIPTION } from '@/lib/reasons';
import { Disagreement } from '@/lib/api';
import { TableColgroup, TableHeaderRow } from './tableColumns';

export function DisagreementsTable({ rows }: { rows: Disagreement[] | undefined }) {
  return (
    <div className={styles.tableWrap}>
      <table>
        <TableColgroup />
        <thead>
          <TableHeaderRow styles={styles} />
        </thead>
        <tbody>
          {rows &&
            rows.map((row) => (
              <tr key={`${row.reason}-${row.record_ref}-${row.entry_ids.join(',')}`}>
                <td>
                  <span
                    className={`${styles.badge} ${styles[row.reason] ?? ''}`}
                    title={REASON_DESCRIPTION[row.reason]}
                  >
                    {REASON_LABEL[row.reason] ?? row.reason}
                  </span>
                </td>
                <td>{row.record_ref}</td>
                <td>
                  {row.location_name ?? row.location_id}
                  {row.location_name && <span className={styles.muted}> ({row.location_id})</span>}
                </td>
                <td className={styles.value}>{row.system_a_value || '—'}</td>
                <td className={styles.value}>
                  {row.system_b_value
                    ? row.system_b_value.split('; ').map((value, i) => (
                        <span key={i} className={styles.stackedValue}>
                          {value}
                        </span>
                      ))
                    : '—'}
                </td>
              </tr>
            ))}
        </tbody>
      </table>
      {rows && rows.length === 0 && (
        <div className={styles.empty}>No disagreements for this org/filter.</div>
      )}
    </div>
  );
}
