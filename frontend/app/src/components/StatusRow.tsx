import type { DashboardStatus } from "../state/dashboardState";

export function StatusRow({ status }: { status: DashboardStatus }) {
  return (
    <section className="status-row" aria-live="polite">
      <div className={`status-pill ${status.tone}`.trim()}>{status.label}</div>
      <p>{status.message}</p>
    </section>
  );
}
