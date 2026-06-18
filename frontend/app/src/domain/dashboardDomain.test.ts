import { describe, expect, it } from "vitest";
import { normalizeApiBase } from "./apiBase";
import { buildPacketPreview } from "./packet";
import { buildRecentApplicationQuery } from "./recentFilters";
import { demoAudit, demoReviewSummary } from "./demoData";
import {
  dryRunBlockReason,
  hasSubmissionExecutorEvidence,
  isValidUuid,
  visibleStateTransitions,
  workflowReadiness,
} from "./workflow";

describe("dashboard domain logic", () => {
  it("normalizes API base values", () => {
    expect(normalizeApiBase("localhost:8000/health")).toBe("https://localhost:8000");
    expect(normalizeApiBase("http://localhost:8000/")).toBe("http://localhost:8000");
  });

  it("builds recent application filters without backend-specific string handling in components", () => {
    expect(
      buildRecentApplicationQuery({
        state: "Approved",
        recommendation: "recommended",
        company: " ApplyGo ",
        sort: "fit_score:desc",
      }),
    ).toBe("limit=10&state=Approved&recommendation=recommended&company=ApplyGo&sort_by=fit_score&sort_dir=desc");
  });

  it("requires executor evidence before exposing Submitted from Approved", () => {
    const approvedAudit = {
      ...demoAudit,
      application: { ...demoAudit.application, state: "Approved" as const },
      executor_actions: [],
    };

    expect(visibleStateTransitions(approvedAudit.application, approvedAudit).map((transition) => transition.state)).toEqual([
      "Rejected",
    ]);
    expect(hasSubmissionExecutorEvidence(approvedAudit)).toBe(false);
  });

  it("calculates workflow readiness from application, policy, and executor evidence", () => {
    const readiness = workflowReadiness(demoAudit.application.id, demoAudit, demoReviewSummary);

    expect(readiness.hasApplication).toBe(true);
    expect(readiness.hasScore).toBe(true);
    expect(readiness.hasAllowedPolicy).toBe(true);
    expect(isValidUuid(demoAudit.application.id)).toBe(true);
  });

  it("keeps deterministic packet text bounded to preview behavior", () => {
    const packet = buildPacketPreview(demoAudit.application.id, demoAudit, demoReviewSummary);

    expect(packet).toContain("Application Packet Preview");
    expect(packet).toContain("Deterministic Cover Note Draft");
    expect(packet).toContain("Preview generation only");
    expect(packet).not.toContain("Gmail");
  });

  it("explains blocked dry-run policy decisions", () => {
    expect(
      dryRunBlockReason({
        ...demoAudit.policy_decisions[0],
        allowed: false,
        decision: "review",
        required_overrides: ["human approval"],
      }),
    ).toBe("Policy requires review before dry-run: Human approval.");
  });
});
