const demoAudit = {
  application: {
    id: "5f2c4a50-8f75-4d38-a40f-15fd5f8f27d4",
    job_id: "77b2ac60-06b2-4f6f-9a42-9a02d2e18424",
    job: {
      id: "77b2ac60-06b2-4f6f-9a42-9a02d2e18424",
      title: "Backend Platform Engineer",
      company: "ApplyGo Demo Co.",
      location: "Remote",
      source_url: "https://jobs.lever.co/applygo/backend-platform-engineer",
      raw_text: "Build Python APIs with FastAPI, PostgreSQL, automation, and platform workflows.",
      remote_ok: true,
      job_type: "full-time",
      ats_type: "lever",
      salary_raw: "$95,000 - $125,000",
      created_at: "2026-06-13T16:10:00Z",
      updated_at: "2026-06-13T16:10:00Z",
    },
    state: "ApplicationCreated",
    automation_mode: "manual",
    fit_score: 86,
    confidence: "high",
    recommendation: "recommended",
    score_reasons: ["Role title is available for review.", "Relevant technical keywords were found."],
    score_risks: [],
    missing_data: [],
    red_flags: [],
    created_at: "2026-06-13T16:12:00Z",
    updated_at: "2026-06-13T16:24:00Z",
  },
  events: [
    {
      event_type: "application.created",
      actor: "system",
      to_state: "ApplicationCreated",
      payload: { automation_mode: "manual" },
      created_at: "2026-06-13T16:12:00Z",
    },
    {
      event_type: "application.scored",
      actor: "scoring",
      payload: { fit_score: 86, confidence: "high", recommendation: "recommended" },
      created_at: "2026-06-13T16:16:00Z",
    },
    {
      event_type: "policy_decision_logged",
      actor: "policy",
      payload: { decision: "allow", action_type: "send_follow_up_email" },
      created_at: "2026-06-13T16:18:00Z",
    },
    {
      event_type: "executor_attempt_logged",
      actor: "worker",
      payload: { execution_mode: "dry_run", idempotency_key: "dry-run-001" },
      created_at: "2026-06-13T16:20:00Z",
    },
    {
      event_type: "executor_result_logged",
      actor: "worker",
      payload: { status: "planned" },
      created_at: "2026-06-13T16:20:01Z",
    },
  ],
  policy_decisions: [
    {
      id: "6a7f2bd6-cd99-4892-afef-5d3a28a64a7a",
      action_type: "send_follow_up_email",
      mode: "dry_run",
      decision: "allow",
      allowed: true,
      reasons: ["Dry-run mode may plan the action but must not create side effects."],
      created_at: "2026-06-13T16:18:00Z",
    },
  ],
  executor_actions: [
    {
      id: "bbf58d5c-2dc5-411c-bd43-0c48f0d0256b",
      action_type: "send_follow_up_email",
      execution_mode: "dry_run",
      status: "planned",
      idempotency_key: "dry-run-001",
      payload: {
        policy_decision_id: "6a7f2bd6-cd99-4892-afef-5d3a28a64a7a",
        source: "dashboard",
      },
      result: {
        action_type: "send_follow_up_email",
        execution_mode: "dry_run",
        policy_decision_id: "6a7f2bd6-cd99-4892-afef-5d3a28a64a7a",
        side_effects: false,
        planned_steps: [
          "Validate recorded policy decision.",
          "Prepare send_follow_up_email payload.",
          "Record executor result in the audit trail.",
        ],
        requires: ["recorded_policy_decision", "stable_idempotency_key"],
      },
      created_at: "2026-06-13T16:20:00Z",
      completed_at: "2026-06-13T16:20:01Z",
    },
  ],
};

const demoReviewSummary = {
  application: demoAudit.application,
  latest_policy_decision: demoAudit.policy_decisions.at(-1),
  latest_executor_action: demoAudit.executor_actions.at(-1),
  latest_packet_review: null,
  packet_reviews: [],
  event_count: demoAudit.events.length,
  next_states: ["Draft"],
  ready_for_policy: true,
  ready_for_dry_run: true,
  ready_for_submission: false,
};

const stateTransitions = {
  ApplicationCreated: [{ state: "Draft", label: "Move to draft" }],
  Draft: [
    { state: "ReadyForReview", label: "Ready for review" },
    { state: "Archived", label: "Archive" },
  ],
  ReadyForReview: [
    { state: "Approved", label: "Approve" },
    { state: "Rejected", label: "Reject" },
    { state: "Draft", label: "Return to draft" },
  ],
  Approved: [
    { state: "Submitted", label: "Mark submitted" },
    { state: "Rejected", label: "Reject" },
  ],
  Submitted: [{ state: "Archived", label: "Archive" }],
  Rejected: [{ state: "Archived", label: "Archive" }],
  Archived: [],
};

const lifecycleSteps = [
  { state: "ApplicationCreated", label: "Created" },
  { state: "Draft", label: "Draft" },
  { state: "ReadyForReview", label: "Review" },
  { state: "Approved", label: "Approved" },
  { state: "Submitted", label: "Submitted" },
];

const sampleJob = {
  title: "Backend Platform Engineer",
  company: "ApplyGo Demo Co.",
  location: "Remote",
  source_url: "https://jobs.lever.co/applygo/backend-platform-engineer",
  remote_ok: true,
  raw_text:
    "Build Python APIs with FastAPI, PostgreSQL, automation workflows, and platform data services. This is a full-time remote role with a salary range of $95,000 - $125,000. Partner with DevOps and product teams to improve reliable backend delivery.",
};

const elements = {
  form: document.querySelector("#audit-form"),
  intakeForm: document.querySelector("#intake-form"),
  apiBase: document.querySelector("#api-base"),
  applicationId: document.querySelector("#application-id"),
  jobTitle: document.querySelector("#job-title"),
  jobCompany: document.querySelector("#job-company"),
  jobLocation: document.querySelector("#job-location"),
  jobUrl: document.querySelector("#job-url"),
  jobDescription: document.querySelector("#job-description"),
  remoteOk: document.querySelector("#remote-ok"),
  sampleJobButton: document.querySelector("#sample-job-button"),
  recentFiltersForm: document.querySelector("#recent-filters-form"),
  recentStateFilter: document.querySelector("#recent-state-filter"),
  recentRecommendationFilter: document.querySelector("#recent-recommendation-filter"),
  recentCompanyFilter: document.querySelector("#recent-company-filter"),
  recentSortFilter: document.querySelector("#recent-sort-filter"),
  recentApplicationsButton: document.querySelector("#recent-applications-button"),
  recentApplicationsList: document.querySelector("#recent-applications-list"),
  scoreButton: document.querySelector("#score-button"),
  policyButton: document.querySelector("#policy-button"),
  dryRunButton: document.querySelector("#dry-run-button"),
  demoButton: document.querySelector("#demo-button"),
  statusPill: document.querySelector("#status-pill"),
  statusMessage: document.querySelector("#status-message"),
  nextActionStatus: document.querySelector("#next-action-status"),
  nextActionTitle: document.querySelector("#next-action-title"),
  nextActionDetail: document.querySelector("#next-action-detail"),
  lifecycleStepper: document.querySelector("#lifecycle-stepper"),
  workflowHint: document.querySelector("#workflow-hint"),
  stateActions: document.querySelector("#state-actions"),
  applicationSummary: document.querySelector("#application-summary"),
  scoreList: document.querySelector("#score-list"),
  policyList: document.querySelector("#policy-list"),
  executorList: document.querySelector("#executor-list"),
  packetReadinessSummary: document.querySelector("#packet-readiness-summary"),
  packetReadiness: document.querySelector("#packet-readiness"),
  packetPreview: document.querySelector("#packet-preview"),
  packetReviewForm: document.querySelector("#packet-review-form"),
  packetReviewStatus: document.querySelector("#packet-review-status"),
  packetReviewNotes: document.querySelector("#packet-review-notes"),
  packetReviewHistory: document.querySelector("#packet-review-history"),
  copyCoverNoteButton: document.querySelector("#copy-cover-note-button"),
  copyPacketButton: document.querySelector("#copy-packet-button"),
  downloadPacketButton: document.querySelector("#download-packet-button"),
  reviewSummary: document.querySelector("#review-summary"),
  reviewSummaryStatus: document.querySelector("#review-summary-status"),
  timeline: document.querySelector("#timeline"),
  eventCount: document.querySelector("#event-count"),
};

let currentAudit = demoAudit;
let currentReviewSummary = demoReviewSummary;

function formatDate(value) {
  if (!value) return "Not recorded";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function safeJson(value) {
  return escapeHtml(JSON.stringify(value || {}));
}

function setStatus(type, label, message) {
  elements.statusPill.className = `status-pill ${type || ""}`.trim();
  elements.statusPill.textContent = label;
  elements.statusMessage.textContent = message;
}

function isValidUuid(value) {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(
    value,
  );
}

function hasLoadedApplication() {
  const applicationId = currentApplicationId();
  return isValidUuid(applicationId) && currentAudit.application?.id === applicationId;
}

function allowedPolicyDecisionIds() {
  return new Set(
    (currentAudit.policy_decisions || [])
      .filter((decision) => decision.allowed)
      .map((decision) => decision.id),
  );
}

function hasSubmissionExecutorEvidence() {
  const allowedIds = allowedPolicyDecisionIds();
  if (!allowedIds.size) return false;

  return (currentAudit.executor_actions || []).some((action) => {
    const policyDecisionId = action.payload?.policy_decision_id || action.result?.policy_decision_id;
    return allowedIds.has(policyDecisionId) && Boolean(action.result);
  });
}

function workflowReadiness() {
  const hasApplication = hasLoadedApplication();
  const hasScore = Boolean(currentReviewSummary?.ready_for_policy || currentAudit.application?.confidence);
  const latestPolicy = latestPolicyDecision();
  const hasAllowedPolicy = Boolean(
    currentReviewSummary?.ready_for_dry_run || latestAllowedPolicyDecision(),
  );
  const hasSubmissionEvidence = Boolean(
    currentReviewSummary?.ready_for_submission || hasSubmissionExecutorEvidence(),
  );
  const isApproved = currentAudit.application?.state === "Approved";

  return {
    hasApplication,
    hasScore,
    latestPolicy,
    hasAllowedPolicy,
    hasSubmissionEvidence,
    isApproved,
  };
}

function setActionMetadata(button, label, hint) {
  button.title = hint;
  button.setAttribute("aria-label", `${label}. ${hint}`);
}

function visibleStateTransitions(application) {
  const transitions = stateTransitions[application.state] || [];
  if (application.state !== "Approved") return transitions;

  return transitions.filter(
    (transition) => transition.state !== "Submitted" || hasSubmissionExecutorEvidence(),
  );
}

function updateWorkflowReadiness() {
  const {
    hasApplication,
    hasScore,
    latestPolicy,
    hasAllowedPolicy,
    hasSubmissionEvidence,
    isApproved,
  } = workflowReadiness();

  if (!hasApplication) {
    clearStateActions();
  }

  elements.scoreButton.disabled = !hasApplication;
  elements.policyButton.disabled = !hasApplication || !hasScore;
  elements.dryRunButton.disabled = !hasApplication || !hasAllowedPolicy;

  const scoreHint = hasApplication
    ? "Score the application to generate reviewer evidence."
    : "Create or load an application before scoring.";
  const policyHint = !hasApplication
    ? "Create or load an application before policy evaluation."
    : !hasScore
      ? "Score the application before evaluating policy."
      : "Evaluate whether policy allows the dry-run preview.";
  const dryRunHint = !hasApplication
    ? "Create or load an application before dry-run."
    : !hasAllowedPolicy
      ? dryRunBlockReason(latestPolicy)
      : "Plan the approved follow-up action without side effects.";

  setActionMetadata(elements.scoreButton, "Score application", scoreHint);
  setActionMetadata(elements.policyButton, "Evaluate policy", policyHint);
  setActionMetadata(elements.dryRunButton, "Preview action", dryRunHint);

  if (!hasApplication) {
    elements.workflowHint.textContent = "Create or load an application to begin.";
  } else if (!hasScore) {
    elements.workflowHint.textContent = "Score the application before evaluating policy.";
  } else if (isApproved && latestPolicy && !hasAllowedPolicy) {
    elements.workflowHint.textContent = dryRunBlockReason(latestPolicy);
  } else if (isApproved && !hasAllowedPolicy) {
    elements.workflowHint.textContent = "Evaluate policy before dry-run.";
  } else if (isApproved && !hasSubmissionEvidence) {
    elements.workflowHint.textContent = "Dry-run before marking submitted.";
  } else if (isApproved) {
    elements.workflowHint.textContent = "Ready to mark submitted or reject.";
  } else if (latestPolicy && !hasAllowedPolicy) {
    elements.workflowHint.textContent = dryRunBlockReason(latestPolicy);
  } else if (!hasAllowedPolicy) {
    elements.workflowHint.textContent = "Evaluate policy before dry-run.";
  } else {
    elements.workflowHint.textContent = "Ready for dry-run follow-up.";
  }

  renderNextAction();
  renderLifecycleStepper(currentAudit.application || {});
}

function renderSummary(application) {
  const job = application.job || {};
  const nextStateLabels = visibleStateTransitions(application).map((transition) =>
    displayLabel(transition.state),
  );
  const overviewRows = [
    ["Location", job.location],
    ["Remote", job.remote_ok ? "Yes" : null],
    ["Job type", job.job_type],
    ["Salary", job.salary_raw],
    ["State", displayLabel(application.state)],
    ["Next states", nextStateLabels],
    ["Mode", displayLabel(application.automation_mode)],
    ["Confidence", displayLabel(application.confidence)],
    ["Missing data", (application.missing_data || []).map(displayLabel)],
    ["Red flags", (application.red_flags || []).map(displayLabel)],
    ["Created", formatDate(application.created_at)],
    ["Updated", formatDate(application.updated_at)],
  ];
  const technicalRows = [
    ["Application", application.id],
    ["Job", application.job_id],
    ["ATS", job.ats_type],
  ];

  elements.applicationSummary.innerHTML = `
    <div class="application-hero">
      <div class="avatar-tile">${escapeHtml(initials(job.company || job.title || "AP"))}</div>
      <div>
        <strong>${escapeHtml(job.title || "Untitled role")}</strong>
        <span>${escapeHtml(job.company || "Unknown company")}</span>
        <div class="hero-meta">${escapeHtml(summaryMeta(job))}</div>
      </div>
    </div>
    <div class="summary-signal-row">
      <div>
        <span>Fit score</span>
        <strong>${escapeHtml(scoreNumberDisplay(application) || "Not recorded")}</strong>
      </div>
      <div>
        <span>Status</span>
        ${badge(application.state)}
      </div>
    </div>
    <div class="summary-signal-row">
      <div>
        <span>Recommendation</span>
        ${badge(recommendationDisplay(application.recommendation) || "Not recorded")}
      </div>
      <div>
        <span>Next states</span>
        ${badgeGroup(nextStateLabels, "None")}
      </div>
    </div>
    ${detailRows(overviewRows)}
    <details class="technical-details">
      <summary>Technical identifiers</summary>
      ${detailRows(technicalRows)}
    </details>
  `;
}

function scoreDisplay(application) {
  if (!application.fit_score) return null;
  const recommendation = application.recommendation
    ? ` - ${recommendationDisplay(application.recommendation)}`
    : "";
  return `${application.fit_score}${recommendation}`;
}

function scoreNumberDisplay(application) {
  return application.fit_score ? `${application.fit_score}/100` : null;
}

function recommendationDisplay(value) {
  return String(value || "").replace(/_/g, " ");
}

function displayLabel(value) {
  return String(value || "")
    .replace(/_/g, " ")
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replace(/\s+/g, " ")
    .trim();
}

function displayList(values) {
  return (values || []).map(displayLabel).filter(Boolean).join(", ");
}

function initials(value) {
  return String(value || "")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase();
}

function summaryMeta(job) {
  return [job.location, job.job_type, job.salary_raw].filter(Boolean).join(" - ") || "Details pending";
}

function detailRows(rows) {
  return `
    <dl class="detail-list">
      ${rows
        .map(
          ([label, value]) =>
            `<dt>${escapeHtml(label)}</dt><dd>${renderDetailValue(value)}</dd>`,
        )
        .join("")}
    </dl>
  `;
}

function renderDetailValue(value) {
  if (Array.isArray(value)) {
    const items = value.map(displayLabel).filter(Boolean);
    if (!items.length) return escapeHtml("Not recorded");
    return badgeGroup(items);
  }

  return escapeHtml(value || "Not recorded");
}

function badgeGroup(values, emptyLabel = "Not recorded") {
  const items = (values || []).map(displayLabel).filter(Boolean);
  if (!items.length) {
    return `<div class="value-chip-list">${badge(emptyLabel)}</div>`;
  }

  return `<div class="value-chip-list">${items.map((item) => badge(item)).join("")}</div>`;
}

function clearStateActions() {
  elements.stateActions.innerHTML = "";
}

function renderStateActions(application) {
  const transitions = visibleStateTransitions(application);

  if (!hasLoadedApplication() || !transitions.length) {
    clearStateActions();
    return;
  }

  elements.stateActions.innerHTML = transitions
    .map(
      (transition) => `
        <button type="button" data-state-target="${escapeHtml(transition.state)}">
          ${escapeHtml(transition.label)}
        </button>
      `,
    )
    .join("");
}

function nextAction() {
  const {
    hasApplication,
    hasScore,
    latestPolicy,
    hasAllowedPolicy,
    hasSubmissionEvidence,
    isApproved,
  } = workflowReadiness();
  const state = currentAudit.application?.state;

  if (!hasApplication) {
    return {
      status: "Setup",
      title: "Create or load an application",
      detail: "Use Sample job, Create, or Load recent to start the guided workflow.",
    };
  }

  if (!hasScore) {
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

  if (isApproved && !hasAllowedPolicy) {
    return {
      status: "Policy",
      title: latestPolicy && !latestPolicy.allowed ? "Resolve policy review" : "Evaluate policy",
      detail: latestPolicy && !latestPolicy.allowed
        ? dryRunBlockReason(latestPolicy)
        : "Policy must allow the follow-up before previewing executor work.",
    };
  }

  if (isApproved && !hasSubmissionEvidence) {
    return {
      status: "Preview",
      title: "Preview action",
      detail: "Dry-run plans the approved follow-up and records audit evidence with no external side effects.",
    };
  }

  if (isApproved) {
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

function renderNextAction() {
  const action = nextAction();
  elements.nextActionStatus.textContent = action.status;
  elements.nextActionTitle.textContent = action.title;
  elements.nextActionDetail.textContent = action.detail;
}

function renderLifecycleStepper(application) {
  const currentIndex = lifecycleSteps.findIndex((step) => step.state === application.state);

  elements.lifecycleStepper.innerHTML = lifecycleSteps
    .map((step, index) => {
      const isActive = index === currentIndex;
      const isComplete = currentIndex > index;
      const classes = ["lifecycle-step"];
      if (isActive) classes.push("active");
      if (isComplete) classes.push("complete");

      return `
        <li class="${classes.join(" ")}">
          <span class="step-dot" aria-hidden="true"></span>
          <span>${escapeHtml(step.label)}</span>
        </li>
      `;
    })
    .join("");
}

function readinessValue(isReady) {
  return isReady ? badge("ready") : badge("blocked");
}

function renderReviewSummary(summary) {
  if (!summary) {
    elements.reviewSummaryStatus.textContent = "No summary";
    elements.reviewSummary.innerHTML = '<p class="empty">No review summary loaded.</p>';
    return;
  }

  elements.reviewSummaryStatus.textContent = `${summary.event_count || 0} audit events`;
  const latestPolicy = summary.latest_policy_decision;
  const latestExecutor = summary.latest_executor_action;
  const latestPacketReview = summary.latest_packet_review;
  const nextStates = displayList(summary.next_states) || "None";
  const items = [
    {
      label: "Policy",
      ready: summary.ready_for_policy,
      detail: summary.ready_for_policy ? "Score context is available." : "Score before policy.",
    },
    {
      label: "Dry-run",
      ready: summary.ready_for_dry_run,
      detail: latestPolicy ? policyDecisionDetail(latestPolicy) : "Allowed policy decision required.",
    },
    {
      label: "Submission",
      ready: summary.ready_for_submission,
      detail: latestExecutor
        ? `${latestExecutor.status} ${latestExecutor.execution_mode} evidence recorded.`
        : "Executor evidence required.",
    },
    {
      label: "Packet review",
      ready: Boolean(latestPacketReview),
      detail: latestPacketReview
        ? `${packetDecisionLabel(latestPacketReview.decision)} by ${latestPacketReview.reviewed_by}`
        : "Human packet review not recorded.",
    },
    {
      label: "Next states",
      ready: Boolean((summary.next_states || []).length),
      detail: nextStates,
    },
  ];

  elements.reviewSummary.innerHTML = items
    .map(
      (item) => `
        <div class="readiness-item">
          <strong>${escapeHtml(item.label)}</strong>
          ${readinessValue(item.ready)}
          <div class="meta">${escapeHtml(item.detail)}</div>
        </div>
      `,
    )
    .join("");
}

function renderScoreDetails(application) {
  if (!application.fit_score && !application.confidence && !application.recommendation) {
    elements.scoreList.innerHTML = '<p class="empty">No score recorded.</p>';
    return;
  }

  const groups = [
    ["Reasons", application.score_reasons || []],
    ["Risks", application.score_risks || []],
    ["Missing data", application.missing_data || []],
    ["Red flags", application.red_flags || []],
  ];

  elements.scoreList.innerHTML = `
    <div class="score-hero">
      <div class="score-value">
        <strong>${escapeHtml(application.fit_score ?? "-")}</strong>
        <span>/100</span>
      </div>
      <div>
        ${badge(recommendationDisplay(application.recommendation) || "No recommendation")}
        <div class="meta">${escapeHtml(application.confidence || "unknown")} confidence</div>
      </div>
    </div>
    ${groups
      .map(([label, values]) => {
        const content = values.length ? values.join(", ") : "None";
        return `
          <div class="compact-item evidence-item ${values.length ? "has-evidence" : "empty-evidence"}">
            <strong>${escapeHtml(label)}</strong>
            <div class="meta">${escapeHtml(content)}</div>
          </div>
        `;
      })
      .join("")}
  `;
}

function badge(value) {
  const normalized = String(value || "unknown").toLowerCase().replace(/[^a-z0-9_-]/g, "");
  return `<span class="badge ${normalized}">${escapeHtml(displayLabel(value) || "unknown")}</span>`;
}

function compactMeta(label, values) {
  const items = Array.isArray(values) ? values.filter(Boolean) : [];
  if (!items.length) return "";

  return `<div class="meta"><strong>${escapeHtml(label)}:</strong> ${escapeHtml(items.join(", "))}</div>`;
}

function latestExecutorAction() {
  return (currentAudit.executor_actions || []).at(-1);
}

function latestPacketReview() {
  return currentReviewSummary?.latest_packet_review || null;
}

function packetReviewHistory() {
  return currentReviewSummary?.packet_reviews || [];
}

function packetDecisionLabel(value) {
  const labels = {
    approved: "Approved",
    rejected: "Rejected",
    changes_requested: "Changes requested",
  };
  return labels[value] || recommendationDisplay(value);
}

function listText(values, fallback = "None recorded") {
  const items = Array.isArray(values) ? values.filter(Boolean) : [];
  return items.length ? items.join("; ") : fallback;
}

function packetLine(label, value) {
  return `${label}: ${value || "Not recorded"}`;
}

function primaryFitReason(application) {
  return (application.score_reasons || []).find(Boolean) || "the available role evidence is ready for review";
}

function primaryFitRisk(application) {
  return (application.score_risks || []).find(Boolean) || (application.missing_data || []).find(Boolean);
}

function packetReadinessSummaryState() {
  const application = currentAudit.application || {};
  const policy = latestPolicyDecision();
  const executor = latestExecutorAction();
  const review = latestPacketReview();
  const nextStep = nextAction();
  const hasApplication = Boolean(application.id);
  const hasScore = Boolean(application.confidence || application.fit_score);
  const state = application.state;
  const isWorkflowApproved = state === "Approved" || state === "Submitted";

  if (!hasApplication) {
    return {
      tone: "blocked",
      status: "Blocked",
      title: "Create or load an application",
      detail: "Packet readiness starts only after a real application is loaded into the dashboard.",
      next: nextStep.detail,
    };
  }

  if (!hasScore) {
    return {
      tone: "blocked",
      status: "Blocked",
      title: "Score the application first",
      detail: "The packet still needs fit evidence before policy, dry-run, or packet review can be trusted.",
      next: nextStep.detail,
    };
  }

  if (!isWorkflowApproved) {
    return {
      tone: "review",
      status: "Needs human decision",
      title: `Workflow state is ${displayLabel(state)}`,
      detail: "Move through the guided workflow before treating the packet as ready for manual use.",
      next: nextStep.detail,
    };
  }

  if (!policy) {
    return {
      tone: "review",
      status: "Needs human decision",
      title: "Policy review still required",
      detail: "Record a policy decision so the packet has governed permission for the preview action.",
      next: nextStep.detail,
    };
  }

  if (!policy.allowed) {
    return {
      tone: "review",
      status: "Needs human decision",
      title: "Policy review is blocking dry-run",
      detail: dryRunBlockReason(policy),
      next: nextStep.detail,
    };
  }

  if (!executor) {
    return {
      tone: "review",
      status: "Needs human decision",
      title: "Preview action still required",
      detail: "Run the dry-run preview so the packet includes executor evidence with no external side effects.",
      next: nextStep.detail,
    };
  }

  if (!review) {
    return {
      tone: "review",
      status: "Needs human decision",
      title: "Packet review not recorded",
      detail: "A human reviewer still needs to approve, reject, or request changes for this packet.",
      next: "Record a packet review decision after checking the current preview.",
    };
  }

  if (review.decision === "changes_requested") {
    return {
      tone: "blocked",
      status: "Blocked",
      title: "Packet changes requested",
      detail: review.notes || "The latest packet review requested changes before manual use.",
      next: "Update the application evidence or packet notes, then record a new packet review.",
    };
  }

  if (review.decision === "rejected") {
    return {
      tone: "blocked",
      status: "Blocked",
      title: "Packet rejected for manual use",
      detail: review.notes || "The latest packet review rejected this packet.",
      next: "Rework the packet evidence before trying again.",
    };
  }

  return {
    tone: "ready",
    status: "Ready",
    title: "Packet is ready for manual use",
    detail:
      "Approved workflow state, allowed policy, dry-run executor evidence, and human packet approval are all recorded.",
    next: "You can copy or download the packet for a governed manual follow-up.",
  };
}

function buildCoverNoteDraft(application, job) {
  const role = job.title || "this role";
  const company = job.company || "your team";
  const recommendation = recommendationDisplay(application.recommendation) || "pending review";
  const score = scoreNumberDisplay(application);
  const reason = primaryFitReason(application);
  const risk = primaryFitRisk(application);
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

function buildPacketPreview() {
  const application = currentAudit.application || {};
  const job = application.job || {};
  const policy = latestPolicyDecision();
  const executor = latestExecutorAction();
  const result = executor?.result || {};
  const nextActionText = nextAction();

  return [
    "Application Packet Preview",
    "==========================",
    packetLine("Role", job.title),
    packetLine("Company", job.company),
    packetLine("Location", summaryMeta(job)),
    packetLine("Source", job.source_url),
    "",
    "Fit Evidence",
    "------------",
    packetLine("Fit score", scoreNumberDisplay(application)),
    packetLine("Confidence", application.confidence),
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
        ? `${executor.status} ${executor.execution_mode}; side effects: ${result.side_effects === false ? "false" : "not recorded"}`
        : "No executor preview recorded.",
    ),
    packetLine("Safeguards", listText(result.requires)),
    packetLine("Planned steps", listText(result.planned_steps)),
    "",
    "Deterministic Cover Note Draft",
    "------------------------------",
    buildCoverNoteDraft(application, job),
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

function packetReadinessItems() {
  const application = currentAudit.application || {};
  const policy = latestPolicyDecision();
  const executor = latestExecutorAction();
  const review = latestPacketReview();

  return [
    {
      label: "Application",
      state: application.id ? "ready" : "blocked",
      summary: application.id ? "Loaded" : "Missing",
      detail: application.id ? "Loaded into the dashboard" : "Create or load an application",
    },
    {
      label: "Score",
      state: application.confidence || application.fit_score ? "ready" : "blocked",
      summary: application.confidence ? displayLabel(application.confidence) : "Needed",
      detail: application.confidence ? `${application.confidence} confidence` : "Score before review",
    },
    {
      label: "Policy",
      state: !policy ? "blocked" : policy.allowed ? "ready" : "review",
      summary: !policy ? "Needed" : displayLabel(policy.decision),
      detail: !policy
        ? "Evaluate policy"
        : policy.allowed
          ? `${policy.decision} decision`
          : dryRunBlockReason(policy),
    },
    {
      label: "Dry-run",
      state: executor ? "ready" : "blocked",
      summary: executor ? displayLabel(executor.status) : "Pending",
      detail: executor ? `${executor.status} ${executor.execution_mode}` : "Preview action",
    },
    {
      label: "Packet review",
      state: !review ? "review" : review.decision === "approved" ? "ready" : "blocked",
      summary: !review ? "Needed" : packetDecisionLabel(review.decision),
      detail: !review
        ? "Record a human review"
        : review.notes || `${packetDecisionLabel(review.decision)} by ${review.reviewed_by}`,
    },
  ];
}

function renderPacketReadinessSummary() {
  const summary = packetReadinessSummaryState();

  elements.packetReadinessSummary.innerHTML = `
    <article class="packet-readiness-summary-card ${summary.tone}">
      <div class="packet-readiness-summary-header">
        <div>
          <span>Packet readiness</span>
          <strong>${escapeHtml(summary.title)}</strong>
        </div>
        ${badge(summary.status)}
      </div>
      <p>${escapeHtml(summary.detail)}</p>
      <small>${escapeHtml(summary.next)}</small>
    </article>
  `;
}

function renderPacketReadiness() {
  elements.packetReadiness.innerHTML = packetReadinessItems()
    .map(
      (item) => `
        <div class="packet-readiness-item ${item.state}">
          <span>${escapeHtml(item.label)}</span>
          <strong>${escapeHtml(item.summary)}</strong>
          <small>${escapeHtml(item.detail)}</small>
        </div>
      `,
    )
    .join("");
}

function renderPacketPreview() {
  renderPacketReadinessSummary();
  renderPacketReadiness();
  renderPacketReviewControls();
  renderPacketReviewHistory();
  elements.packetPreview.textContent = buildPacketPreview();
}

function renderPacketReviewControls() {
  const review = latestPacketReview();
  const hasApplication = hasLoadedApplication();
  const buttons = elements.packetReviewForm.querySelectorAll("button[type='submit']");

  buttons.forEach((button) => {
    button.disabled = !hasApplication;
    button.title = hasApplication
      ? "Record a human packet review decision without external side effects."
      : "Create or load an application before recording packet review.";
  });
  elements.packetReviewNotes.disabled = !hasApplication;

  if (!hasApplication) {
    elements.packetReviewStatus.textContent =
      "Create or load an application before recording packet review.";
    return;
  }

  if (!review) {
    elements.packetReviewStatus.textContent =
      "No packet review recorded. This does not send email, open a browser, or submit an application.";
    return;
  }

  elements.packetReviewStatus.textContent = `${packetDecisionLabel(review.decision)} by ${review.reviewed_by} from ${review.source}.`;
}

function renderPacketReviewHistory() {
  const reviews = [...packetReviewHistory()].reverse();

  if (!reviews.length) {
    elements.packetReviewHistory.innerHTML =
      '<p class="empty">No packet review history recorded yet.</p>';
    return;
  }

  elements.packetReviewHistory.innerHTML = `
    <div class="packet-review-history-heading">
      <strong>Packet review history</strong>
      <span>${reviews.length} recorded review${reviews.length === 1 ? "" : "s"}</span>
    </div>
    <div class="packet-review-history-list">
      ${reviews
        .map(
          (review) => `
            <article class="compact-item packet-review-history-item">
              <div class="stage-card-header">
                <strong>${escapeHtml(packetDecisionLabel(review.decision))}</strong>
                ${badge(review.decision)}
              </div>
              <div class="meta">${escapeHtml(`Reviewed by ${review.reviewed_by} from ${review.source} on ${formatDate(review.created_at)}`)}</div>
              ${
                review.notes
                  ? `<div class="meta"><strong>Notes:</strong> ${escapeHtml(review.notes)}</div>`
                  : '<div class="meta">No reviewer notes recorded.</div>'
              }
            </article>
          `,
        )
        .join("")}
    </div>
  `;
}

function packetFileName() {
  const application = currentAudit.application || {};
  const job = application.job || {};
  const company = String(job.company || "company").replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "");
  const role = String(job.title || "role").replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "");
  const suffix = String(application.id || "demo").slice(0, 8);
  return `applygo-packet-${company || "company"}-${role || "role"}-${suffix}.txt`.toLowerCase();
}

function downloadTextFile(fileName, text) {
  const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 0);
}

function eventSummary(event) {
  const payload = event.payload || {};

  if (event.from_state || event.to_state) {
    return `State change: ${event.from_state || "none"} -> ${event.to_state || "none"}`;
  }

  if (event.event_type === "application.scored") {
    return `Score: ${payload.fit_score ?? "not recorded"} (${payload.confidence || "unknown confidence"}, ${payload.recommendation || "unknown recommendation"})`;
  }

  if (event.event_type === "policy_decision_logged") {
    return `Policy decision: ${payload.decision || "unknown"} for ${payload.action_type || "unknown action"}`;
  }

  if (event.event_type === "executor_attempt_logged") {
    return `Executor attempt: ${payload.execution_mode || "unknown mode"} (${payload.idempotency_key || "no idempotency key"})`;
  }

  if (event.event_type === "executor_result_logged") {
    return `Executor result: ${payload.status || "unknown status"}`;
  }

  if (event.event_type === "application_packet.reviewed") {
    return `Packet review: ${packetDecisionLabel(payload.decision)} by ${payload.reviewed_by || "human"}`;
  }

  return "Audit event recorded.";
}

function renderPolicy(decisions) {
  if (!decisions.length) {
    elements.policyList.innerHTML = '<p class="empty">No policy decisions recorded.</p>';
    return;
  }

  elements.policyList.innerHTML = decisions
    .map(
      (decision) => `
        <div class="compact-item stage-card">
          <div class="stage-card-header">
            <strong>${escapeHtml(decision.action_type)}</strong>
            ${badge(decision.decision)}
          </div>
          <div class="stage-meta">${escapeHtml(decision.mode)} - ${escapeHtml(formatDate(decision.created_at))}</div>
          ${compactMeta("Reasons", decision.reasons)}
          ${compactMeta("Risks", decision.risks)}
          ${compactMeta("Required overrides", decision.required_overrides)}
        </div>
      `,
    )
    .join("");
}

function renderExecutor(actions) {
  if (!actions.length) {
    elements.executorList.innerHTML = '<p class="empty">No executor actions recorded.</p>';
    return;
  }

  elements.executorList.innerHTML = actions
    .map((action) => {
      const result = action.result || {};
      const sideEffects =
        typeof result.side_effects === "boolean"
          ? `<div class="side-effect-banner ${result.side_effects ? "warning" : "safe"}"><strong>Side effects:</strong> ${result.side_effects ? "yes" : "no"}${result.side_effects ? "" : " - dry-run only"}</div>`
          : "";

      return `
        <div class="compact-item stage-card">
          <div class="stage-card-header">
            <strong>${escapeHtml(action.action_type)}</strong>
            ${badge(action.status)}
          </div>
          <div class="stage-meta">${escapeHtml(action.execution_mode)} - ${escapeHtml(action.idempotency_key)}</div>
          ${sideEffects}
          ${compactMeta("Planned steps", result.planned_steps)}
          ${compactMeta("Requires", result.requires)}
        </div>
      `;
    })
    .join("");
}

function renderTimeline(events) {
  elements.eventCount.textContent = `${events.length} ${events.length === 1 ? "event" : "events"}`;

  if (!events.length) {
    elements.timeline.innerHTML = '<li class="empty">No audit events recorded.</li>';
    return;
  }

  elements.timeline.innerHTML = events
    .map(
      (event) => `
        <li>
          <div class="event-time">${escapeHtml(formatDate(event.created_at))}</div>
          <div class="event-body">
            <strong>${escapeHtml(event.event_type)}</strong>
            <div class="meta">Actor: ${escapeHtml(event.actor || "system")}</div>
            <div class="meta">${escapeHtml(eventSummary(event))}</div>
            <div class="meta">${safeJson(event.payload)}</div>
          </div>
        </li>
      `,
    )
    .join("");
}

function focusLatestTimelineEvent() {
  const latestEvent = elements.timeline.querySelector("li:last-child");

  if (!latestEvent || latestEvent.classList.contains("empty")) {
    return;
  }

  latestEvent.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function renderRecentApplications(applications) {
  if (!applications.length) {
    elements.recentApplicationsList.innerHTML =
      '<p class="empty">No applications found. Adjust filters or create a sample job to continue the guided review.</p>';
    return;
  }

  elements.recentApplicationsList.innerHTML = applications
    .map((application) => {
      const job = application.job || {};
      const title = job.title || "Untitled role";
      const company = job.company || "Unknown company";
      const updated = formatDate(application.updated_at || application.created_at);
      const scoreChip =
        application.fit_score !== null && application.fit_score !== undefined
          ? `<span class="score-chip">Fit ${escapeHtml(application.fit_score)}</span>`
          : "";

      return `
        <button
          type="button"
          class="recent-application"
          data-application-id="${escapeHtml(application.id)}"
        >
          <span>
            <strong>${escapeHtml(title)}</strong>
            <span class="meta">${escapeHtml(company)} - ${escapeHtml(updated)}</span>
          </span>
          <span class="recent-application-meta">
            ${scoreChip}
            ${badge(application.state)}
          </span>
        </button>
      `;
    })
    .join("");
}

function renderAudit(data, reviewSummary = null) {
  currentAudit = data;
  currentReviewSummary = reviewSummary || reviewSummaryFromAudit(data);
  renderSummary(data.application);
  renderReviewSummary(currentReviewSummary);
  renderStateActions(data.application);
  renderScoreDetails(data.application);
  renderPolicy(data.policy_decisions || []);
  renderExecutor(data.executor_actions || []);
  renderPacketPreview();
  renderTimeline(data.events || []);
  updateWorkflowReadiness();
}

function reviewSummaryFromAudit(data) {
  const policyDecisions = data.policy_decisions || [];
  const executorActions = data.executor_actions || [];
  const application = data.application || {};
  const allowedPolicyIds = new Set(
    policyDecisions.filter((decision) => decision.allowed).map((decision) => decision.id),
  );
  const hasSubmissionEvidence = executorActions.some((action) => {
    const policyDecisionId = action.payload?.policy_decision_id || action.result?.policy_decision_id;
    return allowedPolicyIds.has(policyDecisionId) && Boolean(action.result);
  });

  return {
    application,
    latest_policy_decision: policyDecisions.at(-1) || null,
    latest_executor_action: executorActions.at(-1) || null,
    latest_packet_review: data.latest_packet_review || null,
    packet_reviews: data.packet_reviews || [],
    event_count: (data.events || []).length,
    next_states: visibleStateTransitions(application).map((transition) => transition.state),
    ready_for_policy: Boolean(application.confidence),
    ready_for_dry_run: Boolean(policyDecisions.some((decision) => decision.allowed)),
    ready_for_submission: application.state === "Approved" && hasSubmissionEvidence,
  };
}

async function fetchJson(url, options) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    ...options,
  });

  if (!response.ok) {
    const detail = await response.text().catch(() => "");
    throw new Error(`Backend returned ${response.status}${detail ? ": " + detail : ""}`);
  }

  return response.json();
}

function normalizeApiBase(value) {
  let normalized = String(value || "").trim();

  if (!normalized) {
    return "";
  }

  if (!/^https?:\/\//i.test(normalized)) {
    normalized = `https://${normalized}`;
  }

  normalized = normalized.replace(/\/+$/, "");
  normalized = normalized.replace(/\/health$/i, "");
  return normalized;
}

function apiBase() {
  return normalizeApiBase(elements.apiBase.value);
}

function inferApiBaseFromBrowser() {
  const { protocol, hostname, port } = window.location;

  if (hostname === "localhost" || hostname === "127.0.0.1") {
    return `${protocol}//${hostname}:8000`;
  }

  // Served directly from the backend port (8000) — same origin, no CORS needed.
  const codespacesBackend = hostname.match(/^(.*)-8000\.app\.github\.dev$/);
  if (codespacesBackend) {
    return `${protocol}//${hostname}`;
  }

  // Served from a different forwarded port — point to the 8000 backend.
  const codespacesMatch = hostname.match(/^(.*)-\d+\.app\.github\.dev$/);
  if (codespacesMatch) {
    return `${protocol}//${codespacesMatch[1]}-8000.app.github.dev`;
  }

  return elements.apiBase.value;
}

function initializeApiBase() {
  const defaultLocalValue = "http://localhost:8000";
  const currentValue = elements.apiBase.value.trim();

  if (currentValue && currentValue !== defaultLocalValue) {
    return;
  }

  elements.apiBase.value = normalizeApiBase(inferApiBaseFromBrowser());
}

async function createManualApplication() {
  const title = elements.jobTitle.value.trim();
  const company = elements.jobCompany.value.trim();
  const base = apiBase();

  if (!title || !company) {
    setStatus("error", "Missing info", "Role title and company are required.");
    return;
  }

  setStatus("loading", "Creating", "Creating job and application records.");

  try {
    elements.apiBase.value = base;

    const job = await fetchJson(`${base}/jobs`, {
      method: "POST",
      body: JSON.stringify({
        title,
        company,
        location: elements.jobLocation.value.trim() || null,
        source_url: elements.jobUrl.value.trim() || null,
        raw_text: elements.jobDescription.value.trim() || null,
        remote_ok: elements.remoteOk.checked,
      }),
    });

    const application = await fetchJson(`${base}/applications`, {
      method: "POST",
      body: JSON.stringify({
        job_id: job.id,
        automation_mode: "manual",
      }),
    });

    elements.applicationId.value = application.id;
    await loadAudit({ focusTimeline: true });
    await loadRecentApplications({ quiet: true });
    setStatus("", "Created", "Manual application created and audit trail loaded.");
  } catch (error) {
    const hint =
      error.message.includes("Failed to fetch") || error.message.includes("NetworkError")
        ? ` Could not reach ${base}. Check Codespaces port 8000 visibility and auth.`
        : "";
    setStatus("error", "Create failed", `${error.message}.${hint}`);
  }
}

function currentApplicationId() {
  return elements.applicationId.value.trim();
}

function requireApplicationId() {
  const applicationId = currentApplicationId();

  if (!applicationId) {
    setStatus("error", "Missing app", "Load or create an application first.");
    return null;
  }

  if (!isValidUuid(applicationId)) {
    setStatus("error", "Invalid ID", "Application ID must be a valid UUID.");
    return null;
  }

  return applicationId;
}

function loadSampleJob() {
  elements.jobTitle.value = sampleJob.title;
  elements.jobCompany.value = sampleJob.company;
  elements.jobLocation.value = sampleJob.location;
  elements.jobUrl.value = sampleJob.source_url;
  elements.remoteOk.checked = sampleJob.remote_ok;
  elements.jobDescription.value = sampleJob.raw_text;
  setStatus("", "Sample loaded", "Review the sample job, then create the application.");
}

async function loadRecentApplications(options = {}) {
  const base = apiBase();
  elements.apiBase.value = base;

  if (!options.quiet) {
    setStatus("loading", "Loading", "Fetching recent applications from the backend.");
  }

  try {
    renderRecentApplications(await fetchJson(`${base}/applications?${recentApplicationQuery()}`));
    if (!options.quiet) {
      setStatus("", "Loaded", "Recent applications loaded.");
    }
  } catch (error) {
    const hint =
      error.message.includes("Failed to fetch") || error.message.includes("NetworkError")
        ? ` Could not reach ${base}. Check Codespaces port 8000 visibility and auth.`
        : "";
    setStatus("error", "Recent failed", `${error.message}.${hint}`);
  }
}

function recentApplicationQuery() {
  const params = new URLSearchParams({ limit: "10" });
  const state = elements.recentStateFilter.value;
  const recommendation = elements.recentRecommendationFilter.value;
  const company = elements.recentCompanyFilter.value.trim();
  const [sortBy, sortDir] = elements.recentSortFilter.value.split(":");

  if (state) params.set("state", state);
  if (recommendation) params.set("recommendation", recommendation);
  if (company) params.set("company", company);
  params.set("sort_by", sortBy || "updated_at");
  params.set("sort_dir", sortDir || "desc");

  return params.toString();
}

function latestAllowedPolicyDecision() {
  const decisions = currentAudit.policy_decisions || [];
  return decisions
    .filter((decision) => decision.allowed && decision.action_type === "send_follow_up_email")
    .at(-1);
}

function latestPolicyDecision() {
  return (currentAudit.policy_decisions || []).at(-1);
}

function policyDecisionDetail(decision) {
  const requiredOverrides = (decision.required_overrides || []).join(", ");
  const base = `${decision.decision} policy for ${decision.action_type}`;
  return requiredOverrides ? `${base}; requires ${requiredOverrides}` : base;
}

function dryRunBlockReason(decision) {
  if (!decision) return "Evaluate policy before dry-run.";
  if (decision.allowed) return "Ready for dry-run follow-up.";
  const requiredOverrides = displayList(decision.required_overrides);
  return requiredOverrides
    ? `Policy requires review before dry-run: ${requiredOverrides}.`
    : `Policy returned ${displayLabel(decision.decision)}; dry-run requires an allowed policy decision.`;
}

function policyContextFromApplication() {
  const application = currentAudit.application || {};

  if (!application.confidence) {
    return null;
  }

  return {
    confidence: application.confidence,
    fit_score: application.fit_score,
    recommendation: application.recommendation,
    reasons: application.score_reasons || [],
    risks: application.score_risks || [],
    missing_data: application.missing_data || [],
    red_flags: application.red_flags || [],
  };
}

async function scoreApplication() {
  const applicationId = requireApplicationId();
  const base = apiBase();

  if (!applicationId) return;

  setStatus("loading", "Scoring", "Scoring application using deterministic job data.");

  try {
    elements.apiBase.value = base;
    await fetchJson(`${base}/applications/${applicationId}/score`, {
      method: "POST",
      body: JSON.stringify({ actor: "user" }),
    });
    await loadAudit({ focusTimeline: true });
    setStatus("", "Scored", "Application score recorded in the audit trail.");
  } catch (error) {
    const hint =
      error.message.includes("Failed to fetch") || error.message.includes("NetworkError")
        ? ` Could not reach ${base}. Check Codespaces port 8000 visibility and auth.`
        : "";
    setStatus("error", "Score failed", `${error.message}.${hint}`);
  }
}

async function transitionApplicationState(targetState) {
  const applicationId = requireApplicationId();
  const base = apiBase();

  if (!applicationId) return;

  setStatus("loading", "State", `Moving application to ${targetState}.`);

  try {
    elements.apiBase.value = base;
    await fetchJson(`${base}/applications/${applicationId}/state`, {
      method: "PATCH",
      body: JSON.stringify({
        state: targetState,
        actor: "user",
        payload: {
          source: "dashboard",
          previous_state: currentAudit.application?.state || null,
        },
      }),
    });
    await loadAudit({ focusTimeline: true });
    setStatus("", "State updated", `Application moved to ${targetState}.`);
  } catch (error) {
    const hint =
      error.message.includes("Failed to fetch") || error.message.includes("NetworkError")
        ? ` Could not reach ${base}. Check Codespaces port 8000 visibility and auth.`
        : "";
    setStatus("error", "State failed", `${error.message}.${hint}`);
  }
}

async function evaluatePolicy() {
  const applicationId = requireApplicationId();
  const base = apiBase();

  if (!applicationId) return;
  if (!currentAudit.application?.confidence) {
    setStatus("error", "Score needed", "Score the application before evaluating policy.");
    return;
  }

  setStatus("loading", "Policy", "Evaluating dry-run follow-up policy.");

  try {
    elements.apiBase.value = base;
    await fetchJson(`${base}/applications/${applicationId}/policy-decisions`, {
      method: "POST",
      body: JSON.stringify({
        requested_action: "send_follow_up_email",
        worker: "email",
        mode: "dry_run",
        context: policyContextFromApplication(),
      }),
    });
    await loadAudit({ focusTimeline: true });
    setStatus("", "Policy logged", "Policy decision recorded in the audit trail.");
  } catch (error) {
    const hint =
      error.message.includes("Failed to fetch") || error.message.includes("NetworkError")
        ? ` Could not reach ${base}. Check Codespaces port 8000 visibility and auth.`
        : "";
    setStatus("error", "Policy failed", `${error.message}.${hint}`);
  }
}

async function dryRunFollowUp() {
  const applicationId = requireApplicationId();
  const base = apiBase();

  if (!applicationId) return;

  const decision = latestAllowedPolicyDecision();
  if (!decision) {
    setStatus("error", "Policy needed", "Evaluate an allowed policy decision before dry-run.");
    return;
  }

  setStatus("loading", "Dry run", "Planning follow-up action with the executor stub.");

  try {
    elements.apiBase.value = base;
    await fetchJson(`${base}/applications/${applicationId}/executor-actions/dry-run`, {
      method: "POST",
      body: JSON.stringify({
        policy_decision_id: decision.id,
        action_type: "send_follow_up_email",
        idempotency_key: `dashboard-follow-up-${applicationId}`,
        payload: {
          source: "dashboard",
          template: "manual_follow_up",
        },
      }),
    });
    await loadAudit({ focusTimeline: true });
    setStatus("", "Dry-run logged", "Executor dry-run result recorded in the audit trail.");
  } catch (error) {
    const hint =
      error.message.includes("Failed to fetch") || error.message.includes("NetworkError")
        ? ` Could not reach ${base}. Check Codespaces port 8000 visibility and auth.`
        : "";
    setStatus("error", "Dry-run failed", `${error.message}.${hint}`);
  }
}

async function recordPacketReview(decision) {
  const applicationId = requireApplicationId();
  const base = apiBase();

  if (!applicationId) return;

  setStatus("loading", "Review", "Recording human packet review decision.");

  try {
    elements.apiBase.value = base;
    await fetchJson(`${base}/applications/${applicationId}/packet-reviews`, {
      method: "POST",
      body: JSON.stringify({
        decision,
        reviewed_by: "human",
        source: "dashboard",
        notes: elements.packetReviewNotes.value.trim() || null,
      }),
    });
    elements.packetReviewNotes.value = "";
    await loadAudit({ focusTimeline: true });
    setStatus(
      "success",
      "Review recorded",
      "Packet review recorded. No email, browser action, or submission occurred.",
    );
  } catch (error) {
    const hint =
      error.message.includes("Failed to fetch") || error.message.includes("NetworkError")
        ? ` Could not reach ${base}. Check Codespaces port 8000 visibility and auth.`
        : "";
    setStatus("error", "Review failed", `${error.message}.${hint}`);
  }
}

async function loadAudit({ focusTimeline = false } = {}) {
  const applicationId = currentApplicationId();
  const base = apiBase();
  elements.apiBase.value = base;

  if (!applicationId) {
    renderAudit(demoAudit, demoReviewSummary);
    setStatus("", "Demo mode", "Using local demo data until a backend application ID is provided.");
    return;
  }

  if (!isValidUuid(applicationId)) {
    setStatus("error", "Invalid ID", "Application ID must be a valid UUID. Run demo_seed to get one.");
    updateWorkflowReadiness();
    return;
  }

  setStatus("loading", "Loading", "Fetching audit summary from the backend.");

  try {
    const [audit, reviewSummary] = await Promise.all([
      fetchJson(`${base}/applications/${applicationId}/audit`),
      fetchJson(`${base}/applications/${applicationId}/review-summary`),
    ]);
    renderAudit(audit, reviewSummary);
    if (focusTimeline) {
      focusLatestTimelineEvent();
    }
    setStatus("", "Live data", "Audit summary loaded from the backend.");
  } catch (error) {
    renderAudit(demoAudit, demoReviewSummary);
    const hint =
      error.message.includes("Failed to fetch") || error.message.includes("NetworkError")
        ? ` Could not reach ${base}. Check Codespaces port 8000 visibility and auth.`
        : "";
    setStatus("error", "Fallback", `${error.message}.${hint} Showing demo data for review.`);
  }
}

elements.form.addEventListener("submit", (event) => {
  event.preventDefault();
  loadAudit();
});

elements.intakeForm.addEventListener("submit", (event) => {
  event.preventDefault();
  createManualApplication();
});

elements.scoreButton.addEventListener("click", () => {
  scoreApplication();
});

elements.stateActions.addEventListener("click", (event) => {
  const button = event.target.closest("[data-state-target]");
  if (!button) return;
  transitionApplicationState(button.dataset.stateTarget);
});

elements.policyButton.addEventListener("click", () => {
  evaluatePolicy();
});

elements.dryRunButton.addEventListener("click", () => {
  dryRunFollowUp();
});

elements.copyPacketButton.addEventListener("click", async () => {
  const packetText = buildPacketPreview();

  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(packetText);
      setStatus("success", "Packet copied", "Application packet preview copied to clipboard.");
    } catch {
      setStatus("error", "Copy unavailable", "Clipboard permission was denied by the browser.");
    }
    return;
  }

  setStatus("error", "Copy unavailable", "Clipboard access is not available in this browser.");
});

elements.copyCoverNoteButton.addEventListener("click", async () => {
  const application = currentAudit.application || {};
  const coverNoteText = buildCoverNoteDraft(application, application.job || {});

  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(coverNoteText);
      setStatus("success", "Cover note copied", "Deterministic cover-note draft copied to clipboard.");
    } catch {
      setStatus("error", "Copy unavailable", "Clipboard permission was denied by the browser.");
    }
    return;
  }

  setStatus("error", "Copy unavailable", "Clipboard access is not available in this browser.");
});

elements.downloadPacketButton.addEventListener("click", () => {
  downloadTextFile(packetFileName(), buildPacketPreview());
  setStatus("success", "Packet downloaded", "Application packet preview downloaded as a text file.");
});

elements.packetReviewForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const decision = event.submitter?.value;
  if (!decision) return;
  recordPacketReview(decision);
});

elements.demoButton.addEventListener("click", () => {
  elements.applicationId.value = "";
  renderAudit(demoAudit, demoReviewSummary);
  setStatus("", "Demo mode", "Using local demo data until a backend application ID is provided.");
});

elements.sampleJobButton.addEventListener("click", () => {
  loadSampleJob();
});

elements.recentApplicationsButton.addEventListener("click", () => {
  loadRecentApplications();
});

elements.recentFiltersForm.addEventListener("change", () => {
  loadRecentApplications();
});

elements.recentFiltersForm.addEventListener("submit", (event) => {
  event.preventDefault();
  loadRecentApplications();
});

elements.recentApplicationsList.addEventListener("click", (event) => {
  const button = event.target.closest("[data-application-id]");
  if (!button) return;

  elements.applicationId.value = button.dataset.applicationId;
  loadAudit();
});

elements.applicationId.addEventListener("input", () => {
  updateWorkflowReadiness();
});

elements.apiBase.addEventListener("blur", () => {
  elements.apiBase.value = normalizeApiBase(elements.apiBase.value);
});

initializeApiBase();
renderAudit(demoAudit, demoReviewSummary);
