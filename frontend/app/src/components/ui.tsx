import type { ReactNode } from "react";
import { displayLabel } from "../domain/labels";

export function Badge({ value }: { value: unknown }) {
  const label = displayLabel(value) || "Unknown";
  const tone = String(value || "unknown").toLowerCase().replace(/[^a-z0-9_-]/g, "");
  return <span className={`badge ${tone}`}>{label}</span>;
}

export function Panel({
  children,
  className = "",
  id,
  label,
}: {
  children: ReactNode;
  className?: string;
  id?: string;
  label?: string;
}) {
  return (
    <section id={id} className={`panel ${className}`.trim()} aria-label={label}>
      {children}
    </section>
  );
}

export function SectionHeading({
  title,
  meta,
  children,
}: {
  title: string;
  meta?: ReactNode;
  children?: ReactNode;
}) {
  return (
    <div className="section-heading">
      <div>
        <h2>{title}</h2>
        {meta ? <span>{meta}</span> : null}
      </div>
      {children}
    </div>
  );
}

export function EmptyState({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="empty-state">
      <strong>{title}</strong>
      <p>{detail}</p>
    </div>
  );
}

export function DetailList({ rows }: { rows: Array<[string, ReactNode]> }) {
  return (
    <dl className="detail-list">
      {rows.map(([label, value]) => (
        <div className="detail-row" key={label}>
          <dt>{label}</dt>
          <dd>{value || "Not recorded"}</dd>
        </div>
      ))}
    </dl>
  );
}
