import { useQuery } from "@tanstack/react-query";
import { fetchDisagreements, SortOrder } from "@/lib/api";
import { ReasonFilter } from "@/lib/reasons";

export function useDisagreements(orgId: string, reason: ReasonFilter, sort: SortOrder) {
  return useQuery({
    queryKey: ["disagreements", orgId, reason, sort],
    queryFn: () => fetchDisagreements({ orgId, reason, sort }),
    enabled: !!orgId,
    // Keep the old rows on screen while re-filtering or re-sorting, but never across an
    // org change - showing one tenant's rows under another tenant's name is the exact
    // leak this screen exists to prevent.
    placeholderData: (previous, previousQuery) =>
      previousQuery?.queryKey[1] === orgId ? previous : undefined,
  });
}
