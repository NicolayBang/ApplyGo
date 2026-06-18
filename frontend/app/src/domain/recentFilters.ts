import type { RecentApplicationFilters } from "../api/types";

export const DEFAULT_RECENT_FILTERS: RecentApplicationFilters = {
  state: "",
  recommendation: "",
  company: "",
  sort: "updated_at:desc",
};

export function buildRecentApplicationQuery(filters: RecentApplicationFilters): string {
  const params = new URLSearchParams({ limit: "10" });
  const [sortBy, sortDir] = filters.sort.split(":");

  if (filters.state) params.set("state", filters.state);
  if (filters.recommendation) params.set("recommendation", filters.recommendation);
  if (filters.company.trim()) params.set("company", filters.company.trim());
  params.set("sort_by", sortBy || "updated_at");
  params.set("sort_dir", sortDir || "desc");

  return params.toString();
}
