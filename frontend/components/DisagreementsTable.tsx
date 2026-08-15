import styles from './DisagreementsTable.module.css';
import { REASON_LABEL, REASON_DESCRIPTION } from '@/lib/reasons';
import { Disagreement } from '@/lib/api';
import { TableColgroup, TableHeaderRow } from './tableColumns';

function Values({ values }: { values: string[] }) {
  if (values.length === 0) return <>—</>;
  return (
    <>
      {values.map((value, i) => (
        <span key={i} className={styles.stackedValue}>
          {value || '(blank)'}
        </span>
      ))}
    </>
  );
}

function Location({ id, name, redacted }: { id: string | null; name: string | null; redacted: boolean }) {
  if (!id) return <span className={styles.muted}>{redacted ? 'another tenant' : '—'}</span>;
  return (
    <>
      {name ?? id}
      {name && <span className={styles.muted}> ({id})</span>}
    </>
  );
}

function LocationCell({ row }: { row: Disagreement }) {
  // Both systems agree on the location (the common case), or only one system has this
  // record at all - either way one line says everything.
  const oneSided = !row.location_id || !row.b_location_id;
  if (!row.cross_tenant && (row.location_id === row.b_location_id || oneSided)) {
    return <Location id={row.location_id ?? row.b_location_id} name={row.location_name ?? row.b_location_name} redacted={false} />;
  }

  return (
    <>
      <span className={styles.stackedValue}>
        <span className={styles.sideLabel}>A</span>
        <Location id={row.location_id} name={row.location_name} redacted={row.cross_tenant} />
      </span>
      <span className={styles.stackedValue}>
        <span className={styles.sideLabel}>B</span>
        <Location id={row.b_location_id} name={row.b_location_name} redacted={row.cross_tenant} />
      </span>
    </>
  );
}

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
                <td>{row.record_ref || '(blank)'}</td>
                <td className={styles.location}>
                  <LocationCell row={row} />
                </td>
                <td className={styles.value}>
                  <Values values={row.system_a_values} />
                </td>
                <td className={styles.value}>
                  <Values values={row.system_b_values} />
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
