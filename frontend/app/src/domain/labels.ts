const LABEL_OVERRIDES: Record<string, string> = {
  ApplicationCreated: "Created",
  ReadyForReview: "Ready for review",
  needs_review: "Needs review",
  not_recommended: "Not recommended",
  dry_run: "Dry run",
  "full-time": "Full-time",
  "part-time": "Part-time",
};

export function displayLabel(value: unknown): string {
  const raw = String(value ?? "").trim();
  if (!raw) return "";
  if (LABEL_OVERRIDES[raw]) return LABEL_OVERRIDES[raw];

  const normalized = raw
    .replace(/_/g, " ")
    .replace(/-/g, " ")
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase();

  return normalized.charAt(0).toUpperCase() + normalized.slice(1);
}

export function displayList(values: unknown[] | null | undefined): string {
  return (values ?? []).map(displayLabel).filter(Boolean).join(", ");
}

export function recommendationDisplay(value: unknown): string {
  return displayLabel(value);
}

export function packetDecisionLabel(value: unknown): string {
  const labels: Record<string, string> = {
    approved: "Approved",
    rejected: "Rejected",
    changes_requested: "Changes requested",
  };
  const raw = String(value ?? "");
  return labels[raw] ?? recommendationDisplay(raw);
}

export function actorLabel(value: unknown): string {
  const labels: Record<string, string> = {
    system: "System",
    user: "User",
    policy: "Policy engine",
    worker: "Worker",
    scoring: "Scoring",
  };

  const raw = String(value || "system");
  return labels[raw] ?? displayLabel(raw);
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "Not recorded";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function initials(value: string | null | undefined): string {
  return String(value ?? "")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase();
}

export function listText(values: string[] | null | undefined, fallback = "None recorded"): string {
  const items = values?.filter(Boolean) ?? [];
  return items.length ? items.join("; ") : fallback;
}
