import type {
  ApplicationAuditRead,
  ApplicationRead,
  ApplicationReviewSummaryRead,
  ApplicationState,
  ExecutorActionRead,
  PolicyContext,
  PolicyDecisionRead,
} from "../api/types";
import { displayLabel, displayList } from "./labels";

export interface StateTransition {
  state: ApplicationState;
  label: string;
  destructive?: boolean;
}

export interface WorkflowReadiness {
  hasApplication: boolean;
  hasScore: boolean;
  latestPolicy: PolicyDecisionRead | null;
  hasAllowedPolicy: boolean;
  hasSubmissionEvidence: boolean;
  isApproved: boolean;
}

export interface NextAction {
  status: string;
  title: string;
  detail: string;
}

export interface PacketReadinessSummary {
  tone: "ready" | "review" | "blocked";
  status: string;
  title: string;
  detail: string;
  next: string;
}

export const lifecycleSteps: Array<{ state: ApplicationState; label: string }> = [
  { state: "ApplicationCreated", label: "Created" },
  { state: "Draft", label: "Draft" },
  { state: "ReadyForReview", label: "Review" },
  { state: "Approved", label: "Approved" },
  { state: "Submitted", label: "Submitted" },
];

export const stateTransitions: Record<ApplicationState, StateTransition[]> = {
  ApplicationCreated: [{ state: "Draft", label: "Move to draft" }],
  Draft: [
    { state: "ReadyForReview", label: "Ready for review" },
    { state: "Archived", label: "Archive", destructive: true },
  ],
  ReadyForReview: [
    { state: "Approved", label: "Approve" },
    { state: "Rejected", label: "Reject", destructive: true },
    { state: "Draft", label: "Return to draft" },
  ],
  Approved: [
    { state: "Submitted", label: "Mark submitted" },
    { state: "Rejected", label: "Reject", destructive: true },
  ],
  Submitted: [{ state: "Archived", label: "Archive", destructive: true }],
  Rejected: [{ state: "Archived", label: "Archive", destructive: true }],
  Archived: [],
};

export function isValidUuid(value: string): boolean {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value);
}

export function hasLoadedApplication(applicationId: string, audit: ApplicationAuditRead): boolean {
  return isValidUuid(applicationId) && audit.application?.id === applicationId;
}

export function latestPolicyDecision(audit: ApplicationAuditRead): PolicyDecisionRead | null {
  return audit.policy_decisions.at(-1) ?? null;
}

export function latestAllowedPolicyDecision(audit: ApplicationAuditRead): PolicyDecisionRead | null {
  return (
    audit.policy_decisions
      .filter((decision) => decision.allowed && decision.action_type === "send_follow_up_email")
      .at(-1) ?? null
  );
}

export function latestExecutorAction(audit: ApplicationAuditRead): ExecutorActionRead | null {
  return audit.executor_actions.at(-1) ?? null;
}

export function allowedPolicyDecisionIds(audit: ApplicationAuditRead): Set<string> {
  return new Set(audit.policy_decisions.filter((decision) => decision.allowed).map((decision) => decision.id));
}

export function hasSubmissionExecutorEvidence(audit: ApplicationAuditRead): boolean {
  const allowedIds = allowedPolicyDecisionIds(audit);
  if (!allowedIds.size) return false;

  return audit.executor_actions.some((action) => {
    const policyDecisionId = String(action.payload?.policy_decision_id ?? action.result?.policy_decision_id ?? "");
    return allowedIds.has(policyDecisionId) && Boolean(action.result);
  });
}

export function visibleStateTransitions(
  application: ApplicationRead,
  audit: ApplicationAuditRead,
): StateTransition[] {
  const transitions = stateTransitions[application.state] ?? [];
  if (application.state !== "Approved") return transitions;

  return transitions.filter(
    (transition) => transition.state !== "Submitted" || hasSubmissionExecutorEvidence(audit),
  );
}

export function reviewSummaryFromAudit(audit: ApplicationAuditRead): ApplicationReviewSummaryRead {
  const policyDecisions = audit.policy_decisions;
  const executorActions = audit.executor_actions;
  const application = audit.application;

  return {
    application,
    latest_policy_decision: policyDecisions.at(-1) ?? null,
    latest_executor_action: executorActions.at(-1) ?? null,
    latest_packet_review: null,
    packet_reviews: [],
    event_count: audit.events.length,
    next_states: visibleStateTransitions(application, audit).map((transition) => transition.state),
    ready_for_policy: Boolean(application.confidence),
    ready_for_dry_run: policyDecisions.some((decision) => decision.allowed),
    ready_for_submission: application.state === "Approved" && hasSubmissionExecutorEvidence(audit),
  };
}

export function workflowReadiness(
  applicationId: string,
  audit: ApplicationAuditRead,
  reviewSummary: ApplicationReviewSummaryRead,
): WorkflowReadiness {
  const hasApplication = hasLoadedApplication(applicationId, audit);
  const hasScore = Boolean(reviewSummary.ready_for_policy || audit.application.confidence);
  const latestPolicy = latestPolicyDecision(audit);
  const hasAllowedPolicy = Boolean(reviewSummary.ready_for_dry_run || latestAllowedPolicyDecision(audit));
  const hasSubmissionEvidence = Boolean(reviewSummary.ready_for_submission || hasSubmissionExecutorEvidence(audit));
  const isApproved = audit.application.state === "Approved";

  return {
    hasApplication,
    hasScore,
    latestPolicy,
    hasAllowedPolicy,
    hasSubmissionEvidence,
    isApproved,
  };
}

export function dryRunBlockReason(decision: PolicyDecisionRead | null): string {
  if (!decision) return "Evaluate policy before dry-run.";
  if (decision.allowed) return "Ready for dry-run follow-up.";
  const requiredOverrides = displayList(decision.required_overrides);
  return requiredOverrides
    ? `Policy requires review before dry-run: ${requiredOverrides}.`
    : `Policy returned ${displayLabel(decision.decision)}; dry-run requires an allowed policy decision.`;
}

export function nextAction(
  applicationId: string,
  audit: ApplicationAuditRead,
  reviewSummary: ApplicationReviewSummaryRead,
): NextAction {
  const readiness = workflowReadiness(applicationId, audit, reviewSummary);
  const state = audit.application.state;

  if (!readiness.hasApplication) {
    return {
      status: "Setup",
      title: "Create or load an application",
      detail: "Use Sample job, Create, or Load recent to start the guided workflow.",
    };
  }

  if (!readiness.hasScore) {
    return {
      status: "Assess",
      title: "Score this application",
      detail: "A score unlocks policy evaluation and gives reviewers fit context.",
    };
  }

  if (state === "ApplicationCreated") {
    return {
      status: "State",
      title: "Move the application to draft",
      detail: "Use the state control when the application is ready for draft review.",
    };
  }

  if (state === "Draft") {
    return {
      status: "Review",
      title: "Mark ready for review",
      detail: "Advance when the draft has enough evidence for approval review.",
    };
  }

  if (state === "ReadyForReview") {
    return {
      status: "Approval",
      title: "Approve or reject the application",
      detail: "Human approval remains the gate before any submission path.",
    };
  }

  if (readiness.isApproved && !readiness.hasAllowedPolicy) {
    return {
      status: "Policy",
      title:
        readiness.latestPolicy && !readiness.latestPolicy.allowed ? "Resolve policy review" : "Evaluate policy",
      detail:
        readiness.latestPolicy && !readiness.latestPolicy.allowed
          ? dryRunBlockReason(readiness.latestPolicy)
          : "Policy must allow the follow-up before previewing executor work.",
    };
  }

  if (readiness.isApproved && !readiness.hasSubmissionEvidence) {
    return {
      status: "Preview",
      title: "Preview action",
      detail: "Dry-run plans the approved follow-up and records audit evidence with no external side effects.",
    };
  }

  if (readiness.isApproved) {
    return {
      status: "Submit",
      title: "Mark submitted when ready",
      detail: "Submission is available only after approved policy and executor preview evidence.",
    };
  }

  if (state === "Submitted") {
    return {
      status: "Complete",
      title: "Review the audit timeline",
      detail: "The workflow has submission evidence. Keep the timeline for audit review.",
    };
  }

  return {
    status: "Audit",
    title: "Review application evidence",
    detail: "Use the readiness cards, policy decisions, executor actions, and audit timeline.",
  };
}

export function policyContextFromApplication(application: ApplicationRead): PolicyContext | null {
  if (!application.confidence) return null;

  return {
    confidence: application.confidence,
    fit_score: application.fit_score,
    recommendation: application.recommendation,
    reasons: application.score_reasons ?? [],
    risks: application.score_risks ?? [],
    missing_data: application.missing_data ?? [],
    red_flags: application.red_flags ?? [],
  };
}

export function policyDecisionDetail(decision: PolicyDecisionRead): string {
  const requiredOverrides = displayList(decision.required_overrides);
  const base = `${displayLabel(decision.decision)} policy for ${displayLabel(decision.action_type)}`;
  return requiredOverrides ? `${base}; requires ${requiredOverrides}` : base;
}
