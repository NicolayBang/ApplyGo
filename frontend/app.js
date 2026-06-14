const demoAudit = {
  application: {
    id: "5f2c4a50-8f75-4d38-a40f-15fd5f8f27d4",
    job_id: "77b2ac60-06b2-4f6f-9a42-9a02d2e18424",
    job: {
      id: "77b2ac60-06b2-4f6f-9a42-9a02d2e18424",
      title: "Backend Platform Engineer",
      company: "ApplyPilot Demo Co.",
      location: "Remote",
      source_url: "https://jobs.lever.co/applypilot/backend-platform-engineer",
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
      result: {
        action_type: "send_follow_up_email",
        execution_mode: "dry_run",
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

const sampleJob = {
  title: "Backend Platform Engineer",
  company: "ApplyPilot Demo Co.",
  location: "Remote",
  source_url: "https://example.com/jobs/backend-platform-engineer",
  remote_ok: true,
  raw_text:
    "Build Python APIs with FastAPI, PostgreSQL, automation workflows, and platform data services. Partner with DevOps and product teams to improve reliable backend delivery.",
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
  scoreButton: document.querySelector("#score-button"),
  policyButton: document.querySelector("#policy-button"),
  dryRunButton: document.querySelector("#dry-run-button"),
  demoButton: document.querySelector("#demo-button"),
  statusPill: document.querySelector("#status-pill"),
  statusMessage: document.querySelector("#status-message"),
  workflowHint: document.querySelector("#workflow-hint"),
  stateActions: document.querySelector("#state-actions"),
  applicationSummary: document.querySelector("#application-summary"),
  scoreList: document.querySelector("#score-list"),
  policyList: document.querySelector("#policy-list"),
  executorList: document.querySelector("#executor-list"),
  timeline: document.querySelector("#timeline"),
  eventCount: document.querySelector("#event-count"),
};

let currentAudit = demoAudit;

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

function updateWorkflowReadiness() {
  const hasApplication = hasLoadedApplication();
  const hasScore = Boolean(currentAudit.application?.confidence);
  const hasAllowedPolicy = Boolean(latestAllowedPolicyDecision());

  if (!hasApplication) {
    clearStateActions();
  }

  elements.scoreButton.disabled = !hasApplication;
  elements.policyButton.disabled = !hasApplication || !hasScore;
  elements.dryRunButton.disabled = !hasApplication || !hasAllowedPolicy;

  if (!hasApplication) {
    elements.workflowHint.textContent = "Create or load an application to begin.";
  } else if (!hasScore) {
    elements.workflowHint.textContent = "Score the application before evaluating policy.";
  } else if (!hasAllowedPolicy) {
    elements.workflowHint.textContent = "Evaluate policy before dry-run.";
  } else {
    elements.workflowHint.textContent = "Ready for dry-run follow-up.";
  }
}

function renderSummary(application) {
  const job = application.job || {};
  const nextStates = (stateTransitions[application.state] || [])
    .map((transition) => transition.state)
    .join(", ");
  const rows = [
    ["Application", application.id],
    ["Job", application.job_id],
    ["Role", job.title],
    ["Company", job.company],
    ["Location", job.location],
    ["Remote", job.remote_ok ? "Yes" : null],
    ["Job type", job.job_type],
    ["ATS", job.ats_type],
    ["Salary", job.salary_raw],
    ["State", application.state],
    ["Next states", nextStates || "None"],
    ["Mode", application.automation_mode],
    ["Fit score", application.fit_score],
    ["Confidence", application.confidence],
    ["Recommendation", application.recommendation],
    ["Missing data", (application.missing_data || []).join(", ")],
    ["Red flags", (application.red_flags || []).join(", ")],
    ["Created", formatDate(application.created_at)],
    ["Updated", formatDate(application.updated_at)],
  ];

  elements.applicationSummary.innerHTML = rows
    .map(
      ([label, value]) => `<dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value || "Not recorded")}</dd>`,
    )
    .join("");
}

function clearStateActions() {
  elements.stateActions.innerHTML = "";
}

function renderStateActions(application) {
  const transitions = stateTransitions[application.state] || [];

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

  elements.scoreList.innerHTML = groups
    .map(([label, values]) => {
      const content = values.length ? values.join(", ") : "None";
      return `
        <div class="compact-item">
          <strong>${escapeHtml(label)}</strong>
          <div class="meta">${escapeHtml(content)}</div>
        </div>
      `;
    })
    .join("");
}

function badge(value) {
  const normalized = String(value || "unknown").toLowerCase().replace(/[^a-z0-9_-]/g, "");
  return `<span class="badge ${normalized}">${escapeHtml(value || "unknown")}</span>`;
}

function compactMeta(label, values) {
  const items = Array.isArray(values) ? values.filter(Boolean) : [];
  if (!items.length) return "";

  return `<div class="meta"><strong>${escapeHtml(label)}:</strong> ${escapeHtml(items.join(", "))}</div>`;
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
        <div class="compact-item">
          <strong>${escapeHtml(decision.action_type)}</strong>
          ${badge(decision.decision)}
          <div class="meta">${escapeHtml(decision.mode)} - ${escapeHtml(formatDate(decision.created_at))}</div>
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
          ? `<div class="meta"><strong>Side effects:</strong> ${result.side_effects ? "yes" : "no"}</div>`
          : "";

      return `
        <div class="compact-item">
          <strong>${escapeHtml(action.action_type)}</strong>
          ${badge(action.status)}
          <div class="meta">${escapeHtml(action.execution_mode)} - ${escapeHtml(action.idempotency_key)}</div>
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

function renderAudit(data) {
  currentAudit = data;
  renderSummary(data.application);
  renderStateActions(data.application);
  renderScoreDetails(data.application);
  renderPolicy(data.policy_decisions || []);
  renderExecutor(data.executor_actions || []);
  renderTimeline(data.events || []);
  updateWorkflowReadiness();
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
    await loadAudit();
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

function latestAllowedPolicyDecision() {
  const decisions = currentAudit.policy_decisions || [];
  return decisions
    .filter((decision) => decision.allowed && decision.action_type === "send_follow_up_email")
    .at(-1);
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
    await loadAudit();
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
    await loadAudit();
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
    await loadAudit();
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
    await loadAudit();
    setStatus("", "Dry-run logged", "Executor dry-run result recorded in the audit trail.");
  } catch (error) {
    const hint =
      error.message.includes("Failed to fetch") || error.message.includes("NetworkError")
        ? ` Could not reach ${base}. Check Codespaces port 8000 visibility and auth.`
        : "";
    setStatus("error", "Dry-run failed", `${error.message}.${hint}`);
  }
}

async function loadAudit() {
  const applicationId = currentApplicationId();
  const base = apiBase();
  elements.apiBase.value = base;

  if (!applicationId) {
    renderAudit(demoAudit);
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
    renderAudit(await fetchJson(`${base}/applications/${applicationId}/audit`));
    setStatus("", "Live data", "Audit summary loaded from the backend.");
  } catch (error) {
    renderAudit(demoAudit);
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

elements.demoButton.addEventListener("click", () => {
  elements.applicationId.value = "";
  renderAudit(demoAudit);
  setStatus("", "Demo mode", "Using local demo data until a backend application ID is provided.");
});

elements.sampleJobButton.addEventListener("click", () => {
  loadSampleJob();
});

elements.applicationId.addEventListener("input", () => {
  updateWorkflowReadiness();
});

elements.apiBase.addEventListener("blur", () => {
  elements.apiBase.value = normalizeApiBase(elements.apiBase.value);
});

initializeApiBase();
renderAudit(demoAudit);
