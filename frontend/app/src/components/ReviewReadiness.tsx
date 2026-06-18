import type { ApplicationReviewSummaryRead } from "../api/types";
import { Badge, Panel, SectionHeading } from "./ui";
import { displayList, packetDecisionLabel } from "../domain/labels";
import { policyDecisionDetail } from "../domain/workflow";

export function ReviewReadiness({ summary }: { summary: ApplicationReviewSummaryRead }) {
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
      ready: Boolean(summary.next_states.length),
      detail: nextStates,
    },
  ];

  return (
    <Panel id="review" className="review-panel" label="Review readiness">
      <SectionHeading title="Review readiness" meta={`${summary.event_count || 0} audit events`} />
      <div className="readiness-list">
        {items.map((item) => (
          <div className="readiness-item" key={item.label}>
            <strong>{item.label}</strong>
            <Badge value={item.ready ? "ready" : "blocked"} />
            <div className="meta">{item.detail}</div>
          </div>
        ))}
      </div>
    </Panel>
  );
}
