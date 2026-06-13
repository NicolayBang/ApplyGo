const demoAudit = {
  application: {
    id: "5f2c4a50-8f75-4d38-a40f-15fd5f8f27d4",
    job_id: "77b2ac60-06b2-4f6f-9a42-9a02d2e18424",
    state: "ApplicationCreated",
    automation_mode: "manual",
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
      result: { action_type: "send_follow_up_email" },
      created_at: "2026-06-13T16:20:00Z",
      completed_at: "2026-06-13T16:20:01Z",
    },
  ],
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
  remoteOk: document.querySelector("#remote-ok"),
  policyButton: document.querySelector("#policy-button"),
  dryRunButton: document.querySelector("#dry-run-button"),
  demoButton: document.querySelector("#demo-button"),
  statusPill: document.querySelector("#status-pill"),
  statusMessage: document.querySelector("#status-message"),
  applicationSummary: document.querySelector("#application-summary"),
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

function renderSummary(application) {
  const rows = [
    ["Application", application.id],
    ["Job", application.job_id],
    ["State", application.state],
    ["Mode", application.automation_mode],
    ["Created", formatDate(application.created_at)],
    ["Updated", formatDate(application.updated_at)],
  ];

  elements.applicationSummary.innerHTML = rows
    .map(
      ([label, value]) => `<dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value || "Not recorded")}</dd>`,
    )
    .join("");
}

function badge(value) {
  const normalized = String(value || "unknown").toLowerCase().replace(/[^a-z0-9_-]/g, "");
  return `<span class="badge ${normalized}">${escapeHtml(value || "unknown")}</span>`;
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
    .map(
      (action) => `
        <div class="compact-item">
          <strong>${escapeHtml(action.action_type)}</strong>
          ${badge(action.status)}
          <div class="meta">${escapeHtml(action.execution_mode)} - ${escapeHtml(action.idempotency_key)}</div>
        </div>
      `,
    )
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
  renderPolicy(data.policy_decisions || []);
  renderExecutor(data.executor_actions || []);
  renderTimeline(data.events || []);
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

  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(applicationId)) {
    setStatus("error", "Invalid ID", "Application ID must be a valid UUID.");
    return null;
  }

  return applicationId;
}

function latestAllowedPolicyDecision() {
  const decisions = currentAudit.policy_decisions || [];
  return decisions
    .filter((decision) => decision.allowed && decision.action_type === "send_follow_up_email")
    .at(-1);
}

async function evaluatePolicy() {
  const applicationId = requireApplicationId();
  const base = apiBase();

  if (!applicationId) return;

  setStatus("loading", "Policy", "Evaluating dry-run follow-up policy.");

  try {
    elements.apiBase.value = base;
    await fetchJson(`${base}/applications/${applicationId}/policy-decisions`, {
      method: "POST",
      body: JSON.stringify({
        requested_action: "send_follow_up_email",
        worker: "email",
        mode: "dry_run",
        context: {
          confidence: "high",
          reasons: ["Manual dashboard dry-run requested."],
          risks: [],
          missing_data: [],
          red_flags: [],
        },
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

  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(applicationId)) {
    setStatus("error", "Invalid ID", "Application ID must be a valid UUID. Run demo_seed to get one.");
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

elements.apiBase.addEventListener("blur", () => {
  elements.apiBase.value = normalizeApiBase(elements.apiBase.value);
});

initializeApiBase();
renderAudit(demoAudit);
