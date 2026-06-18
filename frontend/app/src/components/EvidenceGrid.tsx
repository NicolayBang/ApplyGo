import type { ApplicationAuditRead } from "../api/types";
import { Badge, DetailList, EmptyState, Panel } from "./ui";
import { displayLabel, formatDate, initials, listText } from "../domain/labels";
import { policyDecisionDetail } from "../domain/workflow";
import { scoreNumberDisplay, summaryMeta } from "../domain/packet";

function TechnicalDetails({ rows }: { rows: Array<[string, string | null | undefined]> }) {
  return (
    <details className="technical-details inline-technical-details">
      <summary>Technical details</summary>
      <DetailList rows={rows} />
    </details>
  );
}

export function EvidenceGrid({ audit }: { audit: ApplicationAuditRead }) {
  const application = audit.application;
  const job = application.job;
  const scoreGroups = [
    ["Reasons", application.score_reasons],
    ["Risks", application.score_risks],
    ["Missing data", application.missing_data],
    ["Red flags", application.red_flags],
  ] as const;

  return (
    <>
      <section className="review-evidence-heading" aria-label="Review evidence overview">
        <div>
          <p className="eyebrow">Review evidence</p>
          <h2>Application, fit, policy, and preview</h2>
        </div>
        <span>Human-readable first. Audit details stay visible.</span>
      </section>
      <section className="summary-grid" aria-label="Review evidence">
        <Panel className="summary-panel">
          <h2>Application</h2>
          <div className="summary-list">
            <div className="application-hero">
              <div className="avatar-tile">{initials(job?.company || job?.title || "AP")}</div>
              <div>
                <strong>{job?.title || "Untitled role"}</strong>
                <span>{job?.company || "Unknown company"}</span>
                <div className="hero-meta">{summaryMeta(job ?? {})}</div>
              </div>
            </div>
            <div className="summary-signal-row">
              <div>
                <span>Fit score</span>
                <strong>{scoreNumberDisplay(application.fit_score) || "Not recorded"}</strong>
              </div>
              <div>
                <span>Status</span>
                <Badge value={application.state} />
              </div>
            </div>
            <DetailList
              rows={[
                ["Location", job?.location],
                ["Remote", job?.remote_ok ? "Yes" : "Not recorded"],
                ["Job type", displayLabel(job?.job_type)],
                ["Salary", job?.salary_raw],
                ["Mode", displayLabel(application.automation_mode)],
                ["Confidence", displayLabel(application.confidence)],
                ["Created", formatDate(application.created_at)],
                ["Updated", formatDate(application.updated_at)],
              ]}
            />
            <TechnicalDetails
              rows={[
                ["Application", application.id],
                ["Job", application.job_id],
                ["Company ID", job?.company_id],
                ["Company source", job?.company_source_text],
                ["ATS", displayLabel(job?.ats_type)],
              ]}
            />
          </div>
        </Panel>
        <Panel>
          <h2>Score details</h2>
          <div className="compact-list">
            {application.fit_score || application.confidence || application.recommendation ? (
              <>
                <div className="score-hero">
                  <div className="score-value">
                    <strong>{application.fit_score ?? "-"}</strong>
                    <span>/100</span>
                  </div>
                  <div>
                    <Badge value={application.recommendation || "No recommendation"} />
                    <div className="meta">{displayLabel(application.confidence || "unknown")} confidence</div>
                  </div>
                </div>
                {scoreGroups.map(([label, values]) => (
                  <div className={`compact-item evidence-item ${values?.length ? "has-evidence" : "empty-evidence"}`} key={label}>
                    <strong>{label}</strong>
                    <div className="meta">{listText(values, "None")}</div>
                  </div>
                ))}
              </>
            ) : (
              <EmptyState title="No score recorded" detail="Run scoring to generate fit evidence." />
            )}
          </div>
        </Panel>
        <Panel>
          <h2>Policy decisions</h2>
          <div className="compact-list">
            {audit.policy_decisions.length ? (
              audit.policy_decisions.map((decision) => (
                <div className="compact-item stage-card" key={decision.id}>
                  <div className="stage-card-header">
                    <strong>{displayLabel(decision.action_type)}</strong>
                    <Badge value={decision.decision} />
                  </div>
                  <div className="stage-meta">Preview rule recorded {formatDate(decision.created_at)}</div>
                  <p className="stage-summary">{decision.reasons.find(Boolean) || policyDecisionDetail(decision)}</p>
                  <TechnicalDetails
                    rows={[
                      ["Mode", displayLabel(decision.mode)],
                      ["Allowed", decision.allowed ? "Yes" : "No"],
                      ["Decision ID", decision.id],
                    ]}
                  />
                </div>
              ))
            ) : (
              <EmptyState title="No policy decisions recorded" detail="Evaluate policy before dry-run." />
            )}
          </div>
        </Panel>
        <Panel>
          <h2>Executor actions</h2>
          <div className="compact-list">
            {audit.executor_actions.length ? (
              audit.executor_actions.map((action) => (
                <div className="compact-item stage-card" key={action.id}>
                  <div className="stage-card-header">
                    <strong>{displayLabel(action.action_type)}</strong>
                    <Badge value={action.status} />
                  </div>
                  <div className="stage-meta">Preview action recorded {formatDate(action.created_at)}</div>
                  <p className="stage-summary">
                    {action.result?.side_effects === false
                      ? `${displayLabel(action.status)} with no external side effects.`
                      : `${displayLabel(action.status)} execution evidence recorded.`}
                  </p>
                  {typeof action.result?.side_effects === "boolean" ? (
                    <div className={`side-effect-banner ${action.result.side_effects ? "warning" : "safe"}`}>
                      <strong>Side effects:</strong> {action.result.side_effects ? "yes" : "no - dry-run only"}
                    </div>
                  ) : null}
                  <TechnicalDetails
                    rows={[
                      ["Mode", displayLabel(action.execution_mode)],
                      ["Run ID", action.idempotency_key],
                      ["Action ID", action.id],
                    ]}
                  />
                </div>
              ))
            ) : (
              <EmptyState title="No preview actions recorded" detail="Run dry-run to capture executor evidence." />
            )}
          </div>
        </Panel>
      </section>
    </>
  );
}
