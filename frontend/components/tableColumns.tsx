export const COLUMN_WIDTHS = ["22%", "12%", "24%", "21%", "21%"];

export function TableColgroup() {
  return (
    <colgroup>
      {COLUMN_WIDTHS.map((width, i) => (
        <col key={i} style={{ width }} />
      ))}
    </colgroup>
  );
}

export function TableHeaderRow({ styles }: { styles: Record<string, string> }) {
  return (
    <tr>
      <th>Reason</th>
      <th>Record</th>
      <th>Location</th>
      <th className={styles.value}>System A value</th>
      <th
        className={styles.value}
        title="When System B has more than one entry for a record, all of its values are stacked here, one per line."
      >
        System B value
      </th>

    </tr>
  );
}
