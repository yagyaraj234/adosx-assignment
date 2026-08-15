import styles from "./DisagreementsTable.module.css";
import skeletonStyles from "./TableSkeleton.module.css";
import { TableColgroup, TableHeaderRow } from "./tableColumns";

export function TableSkeleton({ rows = 6 }: { rows?: number }) {
  return (
    <div className={styles.tableWrap}>
      <table>
        <TableColgroup />
        <thead>
          <TableHeaderRow styles={styles} />
        </thead>
        <tbody>
          {Array.from({ length: rows }).map((_, i) => (
            <tr key={i}>
              {Array.from({ length: 5 }).map((_, j) => (
                <td key={j}>
                  <span className={skeletonStyles.bar} />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
