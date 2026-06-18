import type { ApplicationAuditRead, ApplicationReviewSummaryRead } from "../api/types";
import { displayLabel, listText, packetDecisionLabel, recommendationDisplay } from "./labels";
import {
  dryRunBlockReason,
  latestExecutorAction,
  latestPolicyDecision,
  nextAction,
  policyDecisionDetail,
} from "./workflow";

function packetLine(label: string, value: string | null | undefined): string {
  return `${label}: ${value || "Not recorded"}`;
}

export function scoreNumberDisplay(fitScore: number | null | undefined): string | null {
  return fitScore || fitScore === 0 ? `${fitScore}/100` : null;
}

export function summaryMeta(job: { location?: string | null; job_type?: string | null; salary_raw?: string | null }): string {
  return [job.location, displayLabel(job.job_type), job.salary_raw].filter(Boolean).join(" - ") || "Details pending";
}

function primaryFitReason(audit: ApplicationAuditRead): string {
  return (
    audit.application.score_reasons?.find(Boolean) ??
    "the available role evidence is ready for review"
  );
}

function primaryFitRisk(audit: ApplicationAuditRead): string | undefined {
  return audit.application.score_risks?.find(Boolean) ?? audit.application.missing_data?.find(Boolean);
}

export function buildCoverNoteDraft(audit: ApplicationAuditRead): string {
  const application = audit.application;
  const job = application.job;
  const role = job?.title || "this role";
  const company = job?.company || "your team";
  const recommendation = recommendationDisplay(application.recommendation) || "pending review";
  const score = scoreNumberDisplay(application.fit_score);
  const reason = primaryFitReason(audit);
  const risk = primaryFitRisk(audit);
  const riskSentence = risk
    ? `Before sending, I would review one concern: ${risk}.`
    : "I do not see a recorded blocker in the current packet evidence.";

  return [
    `Hello ${company} team,`,
    "",
    `I am interested in the ${role} opportunity. ApplyGo's current review packet marks this application as ${recommendation}${score ? ` with a ${score} fit score` : ""}.`,
    `The strongest recorded fit signal is that ${reason}.`,
    riskSentence,
    "I would like a human reviewer to confirm the packet before any external follow-up is sent.",
  ].join("\n");
}

export function buildPacketPreview(
  applicationId: string,
  audit: ApplicationAuditRead,
  reviewSummary: ApplicationReviewSummaryRead,
): string {
  const application = audit.application;
  const job = application.job;
  const policy = latestPolicyDecision(audit);
  const executor = latestExecutorAction(audit);
  const result = executor?.result ?? {};
  const nextActionText = nextAction(applicationId, audit, reviewSummary);

  return [
    "Application Packet Preview",
    "==========================",
    packetLine("Role", job?.title),
    packetLine("Company", job?.company),
    packetLine("Location", summaryMeta(job ?? {})),
    packetLine("Source", job?.source_url),
    "",
    "Fit Evidence",
    "------------",
    packetLine("Fit score", scoreNumberDisplay(application.fit_score)),
    packetLine("Confidence", displayLabel(application.confidence)),
    packetLine("Recommendation", recommendationDisplay(application.recommendation)),
    packetLine("Reasons", listText(application.score_reasons)),
    packetLine("Risks", listText(application.score_risks)),
    packetLine("Missing data", listText(application.missing_data)),
    packetLine("Red flags", listText(application.red_flags)),
    "",
    "Governance",
    "----------",
    packetLine("Policy decision", policy ? policyDecisionDetail(policy) : "Evaluate policy before preview."),
    packetLine(
      "Dry-run evidence",
      executor
        ? `${displayLabel(executor.status)} ${displayLabel(executor.execution_mode)}; side effects: ${
            result.side_effects === false ? "false" : "not recorded"
          }`
        : "No executor preview recorded.",
    ),
    packetLine("Safeguards", listText(result.requires)),
    packetLine("Planned steps", listText(result.planned_steps)),
    "",
    "Deterministic Cover Note Draft",
    "------------------------------",
    buildCoverNoteDraft(audit),
    "",
    "Next Human Action",
    "-----------------",
    `${nextActionText.title} - ${nextActionText.detail}`,
    "",
    "Boundary",
    "--------",
    "Preview generation only. Recording packet review does not send email, open a browser, or submit an application.",
  ].join("\n");
}

export function packetFileName(audit: ApplicationAuditRead): string {
  const job = audit.application.job;
  const company = String(job?.company || "company").replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "");
  const role = String(job?.title || "role").replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "");
  const suffix = String(audit.application.id || "demo").slice(0, 8);
  return `applygo-packet-${company || "company"}-${role || "role"}-${suffix}.txt`.toLowerCase();
}

export function packetReadinessSummary(
  applicationId: string,
  audit: ApplicationAuditRead,
  reviewSummary: ApplicationReviewSummaryRead,
) {
  const application = audit.application;
  const policy = latestPolicyDecision(audit);
  const executor = latestExecutorAction(audit);
  const review = reviewSummary.latest_packet_review;
  const nextStep = nextAction(applicationId, audit, reviewSummary);
  const hasApplication = Boolean(application.id);
  const hasScore = Boolean(application.confidence || application.fit_score);
  const state = application.state;
  const isWorkflowApproved = state === "Approved" || state === "Submitted";

  if (!hasApplication) {
    return {
      tone: "blocked" as const,
      status: "Blocked",
      title: "Create or load an application",
      detail: "Packet readiness starts only after a real application is loaded into the dashboard.",
      next: nextStep.detail,
    };
  }

  if (!hasScore) {
    return {
      tone: "blocked" as const,
      status: "Blocked",
      title: "Score the application first",
      detail: "The packet still needs fit evidence before policy, dry-run, or packet review can be trusted.",
      next: nextStep.detail,
    };
  }

  if (!isWorkflowApproved) {
    return {
      tone: "review" as const,
      status: "Needs human decision",
      title: `Workflow state is ${displayLabel(state)}`,
      detail: "Move through the guided workflow before treating the packet as ready for manual use.",
      next: nextStep.detail,
    };
  }

  if (!policy) {
    return {
      tone: "review" as const,
      status: "Needs human decision",
      title: "Policy review still required",
      detail: "Record a policy decision so the packet has governed permission for the preview action.",
      next: nextStep.detail,
    };
  }

  if (!policy.allowed) {
    return {
      tone: "review" as const,
      status: "Needs human decision",
      title: "Policy review is blocking dry-run",
      detail: dryRunBlockReason(policy),
      next: nextStep.detail,
    };
  }

  if (!executor) {
    return {
      tone: "review" as const,
      status: "Needs human decision",
      title: "Preview action still required",
      detail: "Run the dry-run preview so the packet includes executor evidence with no external side effects.",
      next: nextStep.detail,
    };
  }

  if (!review) {
    return {
      tone: "review" as const,
      status: "Needs human decision",
      title: "Packet review not recorded",
      detail: "A human reviewer still needs to approve, reject, or request changes for this packet.",
      next: "Record a packet review decision after checking the current preview.",
    };
  }

  if (review.decision === "changes_requested") {
    return {
      tone: "blocked" as const,
      status: "Blocked",
      title: "Packet changes requested",
      detail: review.notes || "The latest packet review requested changes before manual use.",
      next: "Update the application evidence or packet notes, then record a new packet review.",
    };
  }

  if (review.decision === "rejected") {
    return {
      tone: "blocked" as const,
      status: "Blocked",
      title: "Packet rejected for manual use",
      detail: review.notes || "The latest packet review rejected this packet.",
      next: "Rework the packet evidence before trying again.",
    };
  }

  return {
    tone: "ready" as const,
    status: "Ready",
    title: "Packet is ready for manual use",
    detail:
      "Approved workflow state, allowed policy, dry-run executor evidence, and human packet approval are all recorded.",
    next: "You can copy or download the packet for a governed manual follow-up.",
  };
}

export function packetReviewLabel(value: unknown): string {
  return packetDecisionLabel(value);
}
