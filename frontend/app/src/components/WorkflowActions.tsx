import { FileCheck2, Gauge, ShieldCheck } from "lucide-react";
import type { ApplicationAuditRead, ApplicationReviewSummaryRead, ApplicationState } from "../api/types";
import { Panel, SectionHeading } from "./ui";
import { dryRunBlockReason, visibleStateTransitions, workflowReadiness } from "../domain/workflow";

export function WorkflowActions({
  applicationId,
  audit,
  reviewSummary,
  busy,
  onScore,
  onPolicy,
  onDryRun,
  onTransition,
}: {
  applicationId: string;
  audit: ApplicationAuditRead;
  reviewSummary: ApplicationReviewSummaryRead;
  busy: boolean;
  onScore: () => void;
  onPolicy: () => void;
  onDryRun: () => void;
  onTransition: (state: ApplicationState, destructive: boolean) => void;
}) {
  const readiness = workflowReadiness(applicationId, audit, reviewSummary);
  const transitions = readiness.hasApplication ? visibleStateTransitions(audit.application, audit) : [];

  const workflowHint = !readiness.hasApplication
    ? "Create or load an application to begin."
    : !readiness.hasScore
      ? "Score the application before evaluating policy."
      : readiness.isApproved && !readiness.hasAllowedPolicy
        ? readiness.latestPolicy
          ? dryRunBlockReason(readiness.latestPolicy)
          : "Evaluate policy before dry-run."
        : readiness.isApproved && !readiness.hasSubmissionEvidence
          ? "Dry-run before marking submitted."
          : readiness.isApproved
            ? "Ready to mark submitted or reject."
            : readiness.latestPolicy && !readiness.hasAllowedPolicy
              ? dryRunBlockReason(readiness.latestPolicy)
              : !readiness.hasAllowedPolicy
                ? "Evaluate policy before dry-run."
                : "Ready for dry-run follow-up.";

  return (
    <Panel className="workflow-panel" label="Workflow actions">
      <SectionHeading title="Guided actions" meta="State, score, policy, and dry-run" />
      <p className="workflow-hint">{workflowHint}</p>
      <div className="state-actions">
        {transitions.map((transition) => (
          <button
            type="button"
            className={transition.destructive ? "danger-button" : "secondary-button"}
            key={transition.state}
            disabled={busy}
            onClick={() => onTransition(transition.state, Boolean(transition.destructive))}
          >
            {transition.label}
          </button>
        ))}
      </div>
      <div className="workflow-actions">
        <button type="button" disabled={busy || !readiness.hasApplication} onClick={onScore}>
          <Gauge aria-hidden="true" size={16} />
          Score application
        </button>
        <button type="button" disabled={busy || !readiness.hasApplication || !readiness.hasScore} onClick={onPolicy}>
          <ShieldCheck aria-hidden="true" size={16} />
          Evaluate policy
        </button>
        <button
          type="button"
          title="Plan the approved follow-up action without side effects."
          disabled={busy || !readiness.hasApplication || !readiness.hasAllowedPolicy}
          onClick={onDryRun}
        >
          <FileCheck2 aria-hidden="true" size={16} />
          Preview action
        </button>
      </div>
    </Panel>
  );
}
