import type { EventLogRead } from "../api/types";
import { EmptyState, Panel, SectionHeading } from "./ui";
import { actorLabel, displayLabel, formatDate, packetDecisionLabel } from "../domain/labels";

function eventTitle(event: EventLogRead): string {
  const labels: Record<string, string> = {
    "application.created": "Application created",
    "application.state_changed": "Application state updated",
    "application.scored": "Application scored",
    policy_decision_logged: "Policy decision recorded",
    executor_attempt_logged: "Preview attempt recorded",
    executor_result_logged: "Preview result recorded",
    "application_packet.reviewed": "Packet review recorded",
  };

  return labels[event.event_type] ?? displayLabel(event.event_type) ?? "Audit event";
}

function eventSummary(event: EventLogRead): string {
  const payload = event.payload ?? {};

  if (event.from_state || event.to_state) {
    return `State change: ${displayLabel(event.from_state || "none")} -> ${displayLabel(event.to_state || "none")}`;
  }

  if (event.event_type === "application.scored") {
    return `Score: ${String(payload.fit_score ?? "not recorded")} (${displayLabel(payload.confidence || "unknown confidence")}, ${displayLabel(payload.recommendation || "unknown recommendation")})`;
  }

  if (event.event_type === "policy_decision_logged") {
    return `Policy decision: ${displayLabel(payload.decision || "unknown")} for ${displayLabel(payload.action_type || "unknown action")}`;
  }

  if (event.event_type === "executor_attempt_logged") {
    return `Executor attempt: ${displayLabel(payload.execution_mode || "unknown mode")} (${String(payload.idempotency_key || "no idempotency key")})`;
  }

  if (event.event_type === "executor_result_logged") {
    return `Executor result: ${displayLabel(payload.status || "unknown status")}`;
  }

  if (event.event_type === "application_packet.reviewed") {
    return `Packet review: ${packetDecisionLabel(payload.decision)} by ${String(payload.reviewed_by || "human")}`;
  }

  return "Audit event recorded.";
}

export function AuditTimeline({ events }: { events: EventLogRead[] }) {
  return (
    <Panel id="timeline" className="timeline-panel" label="Audit timeline">
      <SectionHeading title="Audit timeline" meta={`${events.length} ${events.length === 1 ? "event" : "events"}`} />
      <ol className="timeline">
        {events.length ? (
          events.map((event, index) => (
            <li key={`${event.created_at}-${event.event_type}-${index}`}>
              <div className="event-time">{formatDate(event.created_at)}</div>
              <div className="event-body">
                <strong>{eventTitle(event)}</strong>
                <div className="meta">Actor: {actorLabel(event.actor || "system")}</div>
                <div className="meta">Event key: {event.event_type}</div>
                <div className="meta">{eventSummary(event)}</div>
                <div className="meta">{JSON.stringify(event.payload ?? {})}</div>
              </div>
            </li>
          ))
        ) : (
          <li className="empty">
            <EmptyState title="No audit events recorded" detail="Load an application or use demo data to inspect the workflow timeline." />
          </li>
        )}
      </ol>
    </Panel>
  );
}
