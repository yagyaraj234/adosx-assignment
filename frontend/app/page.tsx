"use client";

import { useState } from "react";
import styles from "./page.module.css";
import { SortOrder } from "@/lib/api";
import { ReasonFilter } from "@/lib/reasons";
import { useOrgs } from "@/hooks/useOrgs";
import { useDisagreements } from "@/hooks/useDisagreements";
import { Toolbar } from "@/components/Toolbar";
import { ErrorBanner } from "@/components/ErrorBanner";
import { DisagreementsTable } from "@/components/DisagreementsTable";
import { TableSkeleton } from "@/components/TableSkeleton";

const API_ERROR_MESSAGE = "Could not reach the API. Is the backend running on :8000?";

export default function Home() {
  const [orgId, setOrgId] = useState("");
  const [reason, setReason] = useState<ReasonFilter>("");
  const [sort, setSort] = useState<SortOrder>("value");

  const orgsQuery = useOrgs();
  const orgs = orgsQuery.data ?? [];
  const activeOrgId = orgId || orgs[0] || "";

  const disagreementsQuery = useDisagreements(activeOrgId, reason, sort);
  const rows = disagreementsQuery.data;

  return (
    <main className={styles.page}>
      <div className={styles.header}>
        <h1>Disagreements</h1>
        <p className={styles.subtitle}>
          Records where System A and System B disagree, scoped to one tenant at a time.
        </p>
      </div>

      {orgsQuery.isError && <ErrorBanner message={API_ERROR_MESSAGE} />}

      {orgsQuery.isSuccess && orgs.length === 0 && (
        <ErrorBanner message="No orgs found. Nothing to compare yet." />
      )}

      <Toolbar
        orgs={orgs}
        orgId={activeOrgId}
        onOrgChange={setOrgId}
        reason={reason}
        onReasonChange={setReason}
        sort={sort}
        onSortChange={setSort}
        disabled={orgsQuery.isLoading || orgs.length === 0}
      />

      {disagreementsQuery.isError ? (
        <ErrorBanner message={API_ERROR_MESSAGE} />
      ) : rows === undefined ? (
        <>
          <p className={styles.summary}>Loading…</p>
          <TableSkeleton />
        </>
      ) : (
        <>
          <p className={styles.summary}>
            {rows.length} disagreement{rows.length === 1 ? "" : "s"}
            {disagreementsQuery.isFetching && " · refreshing…"}
          </p>

          <div className={disagreementsQuery.isFetching ? styles.refreshing : undefined}>
            <DisagreementsTable rows={rows} />
          </div>
        </>
      )}
    </main>
  );
}
