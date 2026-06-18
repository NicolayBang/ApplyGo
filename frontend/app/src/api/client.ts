import type {
  ApplicationAuditRead,
  ApplicationPacketReviewCreate,
  ApplicationPacketReviewRead,
  ApplicationRead,
  ApplicationReviewSummaryRead,
  ApplicationScoreRequest,
  ApplicationStateUpdate,
  ExecutorActionRead,
  ExecutorDryRunRequest,
  JobCreate,
  JobRead,
  PolicyDecisionRead,
  PolicyEvaluationRequest,
  RecentApplicationFilters,
} from "./types";
import { buildRecentApplicationQuery } from "../domain/recentFilters";
import { normalizeApiBase } from "../domain/apiBase";

export class ApiClient {
  private readonly base: string;

  constructor(base: string) {
    this.base = normalizeApiBase(base);
  }

  async createJob(payload: JobCreate): Promise<JobRead> {
    return this.fetchJson<JobRead>("/jobs", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async createApplication(jobId: string): Promise<ApplicationRead> {
    return this.fetchJson<ApplicationRead>("/applications", {
      method: "POST",
      body: JSON.stringify({ job_id: jobId, automation_mode: "manual" }),
    });
  }

  async listApplications(filters: RecentApplicationFilters): Promise<ApplicationRead[]> {
    return this.fetchJson<ApplicationRead[]>(`/applications?${buildRecentApplicationQuery(filters)}`);
  }

  async updateApplicationState(applicationId: string, payload: ApplicationStateUpdate): Promise<ApplicationRead> {
    return this.fetchJson<ApplicationRead>(`/applications/${applicationId}/state`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  }

  async scoreApplication(applicationId: string, payload: ApplicationScoreRequest): Promise<ApplicationRead> {
    return this.fetchJson<ApplicationRead>(`/applications/${applicationId}/score`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async evaluatePolicy(applicationId: string, payload: PolicyEvaluationRequest): Promise<PolicyDecisionRead> {
    return this.fetchJson<PolicyDecisionRead>(`/applications/${applicationId}/policy-decisions`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async dryRunExecutor(applicationId: string, payload: ExecutorDryRunRequest): Promise<ExecutorActionRead> {
    return this.fetchJson<ExecutorActionRead>(`/applications/${applicationId}/executor-actions/dry-run`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async recordPacketReview(
    applicationId: string,
    payload: ApplicationPacketReviewCreate,
  ): Promise<ApplicationPacketReviewRead> {
    return this.fetchJson<ApplicationPacketReviewRead>(`/applications/${applicationId}/packet-reviews`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async getAudit(applicationId: string): Promise<ApplicationAuditRead> {
    return this.fetchJson<ApplicationAuditRead>(`/applications/${applicationId}/audit`);
  }

  async getReviewSummary(applicationId: string): Promise<ApplicationReviewSummaryRead> {
    return this.fetchJson<ApplicationReviewSummaryRead>(`/applications/${applicationId}/review-summary`);
  }

  private async fetchJson<T>(path: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${this.base}${path}`, {
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      ...options,
    });

    if (!response.ok) {
      const detail = await response.text().catch(() => "");
      throw new Error(`Backend returned ${response.status}${detail ? `: ${detail}` : ""}`);
    }

    return response.json() as Promise<T>;
  }
}

export function apiClient(base: string): ApiClient {
  return new ApiClient(base);
}
