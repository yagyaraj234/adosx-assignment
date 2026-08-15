import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { fetchDisagreements, SortOrder } from "@/lib/api";
import { ReasonFilter } from "@/lib/reasons";

export function useDisagreements(orgId: string, reason: ReasonFilter, sort: SortOrder) {
  return useQuery({
    queryKey: ["disagreements", orgId, reason, sort],
    queryFn: () => fetchDisagreements({ orgId, reason, sort }),
    enabled: !!orgId,
    placeholderData: keepPreviousData,
  });
}
