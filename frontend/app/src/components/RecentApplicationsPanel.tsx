import type { ApplicationRead, RecentApplicationFilters } from "../api/types";
import { Badge, EmptyState, Panel, SectionHeading } from "./ui";
import { formatDate } from "../domain/labels";

export function RecentApplicationsPanel({
  applications,
  filters,
  isLoading,
  onFiltersChange,
  onLoad,
  onSelect,
}: {
  applications: ApplicationRead[];
  filters: RecentApplicationFilters;
  isLoading: boolean;
  onFiltersChange: (filters: RecentApplicationFilters) => void;
  onLoad: () => void;
  onSelect: (applicationId: string) => void;
}) {
  return (
    <Panel id="applications" className="recent-panel" label="Recent applications">
      <SectionHeading title="Recent applications">
        <button type="button" onClick={onLoad} disabled={isLoading}>
          {isLoading ? "Loading" : "Load recent"}
        </button>
      </SectionHeading>
      <form
        className="recent-filters"
        onSubmit={(event) => {
          event.preventDefault();
          onLoad();
        }}
      >
        <label>
          <span>State</span>
          <select
            value={filters.state}
            onChange={(event) => onFiltersChange({ ...filters, state: event.target.value as RecentApplicationFilters["state"] })}
          >
            <option value="">Any state</option>
            <option value="ApplicationCreated">Created</option>
            <option value="Draft">Draft</option>
            <option value="ReadyForReview">Ready for review</option>
            <option value="Approved">Approved</option>
            <option value="Submitted">Submitted</option>
            <option value="Rejected">Rejected</option>
            <option value="Archived">Archived</option>
          </select>
        </label>
        <label>
          <span>Recommendation</span>
          <select
            value={filters.recommendation}
            onChange={(event) => onFiltersChange({ ...filters, recommendation: event.target.value })}
          >
            <option value="">Any recommendation</option>
            <option value="recommended">Recommended</option>
            <option value="needs_review">Needs review</option>
            <option value="not_recommended">Not recommended</option>
          </select>
        </label>
        <label>
          <span>Company</span>
          <input
            type="search"
            placeholder="Search company"
            value={filters.company}
            onChange={(event) => onFiltersChange({ ...filters, company: event.target.value })}
          />
        </label>
        <label>
          <span>Sort</span>
          <select value={filters.sort} onChange={(event) => onFiltersChange({ ...filters, sort: event.target.value })}>
            <option value="updated_at:desc">Recently updated</option>
            <option value="created_at:desc">Recently created</option>
            <option value="fit_score:desc">Fit score high first</option>
            <option value="fit_score:asc">Fit score low first</option>
            <option value="state:asc">State A-Z</option>
          </select>
        </label>
      </form>
      <div className="recent-applications-list">
        {applications.length ? (
          applications.map((application) => {
            const job = application.job;
            const score = application.fit_score !== null && application.fit_score !== undefined;
            return (
              <button
                type="button"
                className="recent-application"
                key={application.id}
                onClick={() => onSelect(application.id)}
              >
                <span>
                  <strong>{job?.title || "Untitled role"}</strong>
                  <span className="meta">
                    {job?.company || "Unknown company"} - {formatDate(application.updated_at || application.created_at)}
                  </span>
                </span>
                <span className="recent-application-meta">
                  {score ? <span className="score-chip">Fit {application.fit_score}</span> : null}
                  <Badge value={application.state} />
                </span>
              </button>
            );
          })
        ) : (
          <EmptyState
            title="No applications loaded"
            detail="Load recent applications or create a sample job to start a guided review."
          />
        )}
      </div>
    </Panel>
  );
}
