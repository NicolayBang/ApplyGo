export type ApplicationState =
  | "ApplicationCreated"
  | "Draft"
  | "ReadyForReview"
  | "Approved"
  | "Submitted"
  | "Rejected"
  | "Archived";

export type AutomationMode = "manual" | "semi_auto" | "full_auto" | string;
export type ConfidenceLevel = "high" | "medium" | "low" | string;
export type Recommendation = "recommended" | "needs_review" | "not_recommended" | string;
export type PolicyDecisionValue = "allow" | "review" | "deny" | string;
export type PacketReviewDecision = "approved" | "rejected" | "changes_requested";

export interface JobRead {
  id: string;
  source_url: string | null;
  raw_text: string | null;
  title: string | null;
  company: string | null;
  company_id?: string | null;
  company_source_text?: string | null;
  location: string | null;
  remote_ok: boolean;
  job_type: string | null;
  ats_type: string | null;
  salary_raw: string | null;
  created_at: string;
  updated_at: string;
}

export interface JobCreate {
  source_url?: string | null;
  raw_text?: string | null;
  title?: string | null;
  company?: string | null;
  location?: string | null;
  remote_ok?: boolean;
}

export interface ApplicationRead {
  id: string;
  job_id: string;
  job: JobRead | null;
  state: ApplicationState;
  automation_mode: AutomationMode;
  fit_score: number | null;
  confidence: ConfidenceLevel | null;
  recommendation: Recommendation | null;
  score_reasons: string[] | null;
  score_risks: string[] | null;
  missing_data: string[] | null;
  red_flags: string[] | null;
  created_at: string;
  updated_at: string;
}

export interface EventLogRead {
  id?: string;
  application_id?: string;
  event_type: string;
  actor: string;
  from_state?: string | null;
  to_state?: string | null;
  payload?: Record<string, unknown> | null;
  created_at: string;
}

export interface PolicyDecisionRead {
  id: string;
  action_type: string;
  mode: string;
  decision: PolicyDecisionValue;
  allowed: boolean;
  reasons: string[];
  risks?: string[] | null;
  required_overrides?: string[] | null;
  created_at: string;
}

export interface ExecutorActionRead {
  id: string;
  action_type: string;
  execution_mode: string;
  status: string;
  idempotency_key: string;
  payload: Record<string, unknown> | null;
  result: ExecutorResult | null;
  created_at: string;
  completed_at: string | null;
}

export interface ExecutorResult {
  action_type?: string;
  execution_mode?: string;
  policy_decision_id?: string;
  side_effects?: boolean;
  planned_steps?: string[];
  requires?: string[];
  status?: string;
  [key: string]: unknown;
}

export interface ApplicationPacketReviewRead {
  id: string;
  application_id: string;
  decision: PacketReviewDecision;
  reviewed_by: string;
  source: string;
  packet_text: string | null;
  notes: string | null;
  created_at: string;
}

export interface ApplicationAuditRead {
  application: ApplicationRead;
  events: EventLogRead[];
  policy_decisions: PolicyDecisionRead[];
  executor_actions: ExecutorActionRead[];
}

export interface ApplicationReviewSummaryRead {
  application: ApplicationRead;
  latest_policy_decision: PolicyDecisionRead | null;
  latest_executor_action: ExecutorActionRead | null;
  latest_packet_review: ApplicationPacketReviewRead | null;
  packet_reviews: ApplicationPacketReviewRead[];
  event_count: number;
  next_states: ApplicationState[];
  ready_for_policy: boolean;
  ready_for_dry_run: boolean;
  ready_for_submission: boolean;
}

export interface ApplicationStateUpdate {
  state: ApplicationState;
  actor: string;
  payload: Record<string, unknown>;
}

export interface ApplicationScoreRequest {
  actor: string;
}

export interface PolicyEvaluationRequest {
  requested_action: string;
  worker: string;
  mode: "dry_run";
  context: PolicyContext | null;
  actor?: string;
}

export interface PolicyContext {
  confidence: ConfidenceLevel;
  fit_score: number | null;
  recommendation: Recommendation | null;
  reasons: string[];
  risks: string[];
  missing_data: string[];
  red_flags: string[];
}

export interface ExecutorDryRunRequest {
  policy_decision_id: string;
  action_type: string;
  idempotency_key: string;
  payload: Record<string, unknown>;
  worker?: string;
  actor?: string;
}

export interface ApplicationPacketReviewCreate {
  decision: PacketReviewDecision;
  reviewed_by: string;
  source: "dashboard";
  packet_text?: string | null;
  notes?: string | null;
}

export interface RecentApplicationFilters {
  state: ApplicationState | "";
  recommendation: Recommendation | "";
  company: string;
  sort: string;
}

export interface DashboardData {
  audit: ApplicationAuditRead;
  reviewSummary: ApplicationReviewSummaryRead;
}
