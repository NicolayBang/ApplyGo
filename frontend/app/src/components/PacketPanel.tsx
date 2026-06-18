import { Clipboard, Copy, Download } from "lucide-react";
import type { ApplicationAuditRead, ApplicationReviewSummaryRead, PacketReviewDecision } from "../api/types";
import { Badge, EmptyState, Panel, SectionHeading } from "./ui";
import { formatDate, packetDecisionLabel } from "../domain/labels";
import {
  buildCoverNoteDraft,
  buildPacketPreview,
  packetFileName,
  packetReadinessSummary,
  packetReviewLabel,
} from "../domain/packet";

export function PacketPanel({
  applicationId,
  audit,
  reviewSummary,
  notes,
  busy,
  onNotesChange,
  onCopy,
  onDownload,
  onReview,
}: {
  applicationId: string;
  audit: ApplicationAuditRead;
  reviewSummary: ApplicationReviewSummaryRead;
  notes: string;
  busy: boolean;
  onNotesChange: (value: string) => void;
  onCopy: (text: string, successMessage: string) => void;
  onDownload: (fileName: string, text: string) => void;
  onReview: (decision: PacketReviewDecision) => void;
}) {
  const summary = packetReadinessSummary(applicationId, audit, reviewSummary);
  const packetText = buildPacketPreview(applicationId, audit, reviewSummary);
  const review = reviewSummary.latest_packet_review;
  const history = [...reviewSummary.packet_reviews].reverse();
  const hasApplication = Boolean(applicationId && audit.application.id === applicationId);

  return (
    <Panel id="packet" className="packet-panel" label="Application packet preview">
      <SectionHeading title="Application packet" meta="Generated preview from current review evidence">
        <div className="packet-actions">
          <button
            type="button"
            className="secondary-button"
            onClick={() => onCopy(buildCoverNoteDraft(audit), "Deterministic cover-note draft copied to clipboard.")}
          >
            <Copy aria-hidden="true" size={16} />
            Copy cover note
          </button>
          <button
            type="button"
            className="secondary-button"
            onClick={() => onCopy(packetText, "Application packet preview copied to clipboard.")}
          >
            <Clipboard aria-hidden="true" size={16} />
            Copy packet
          </button>
          <button type="button" className="secondary-button" onClick={() => onDownload(packetFileName(audit), packetText)}>
            <Download aria-hidden="true" size={16} />
            Download packet
          </button>
        </div>
      </SectionHeading>
      <p className="packet-note">
        Preview only. This does not save packet content, send email, open a browser, or submit an application.
      </p>
      <div className="packet-readiness-summary">
        <article className={`packet-readiness-summary-card ${summary.tone}`}>
          <div className="packet-readiness-summary-header">
            <div>
              <span>Packet readiness</span>
              <strong>{summary.title}</strong>
            </div>
            <Badge value={summary.status} />
          </div>
          <p>{summary.detail}</p>
          <small>{summary.next}</small>
        </article>
      </div>
      <form
        className="packet-review-form"
        onSubmit={(event) => {
          event.preventDefault();
          const decision = (event.nativeEvent as SubmitEvent).submitter?.getAttribute("value") as PacketReviewDecision | null;
          if (decision) onReview(decision);
        }}
      >
        <div>
          <strong>Human packet review</strong>
          <p>
            {!hasApplication
              ? "Create or load an application before recording packet review."
              : review
                ? `${packetDecisionLabel(review.decision)} by ${review.reviewed_by} from ${review.source}.`
                : "No packet review recorded. This does not send email, open a browser, or submit an application."}
          </p>
        </div>
        <label>
          <span>Reviewer notes</span>
          <textarea
            rows={3}
            value={notes}
            disabled={!hasApplication || busy}
            placeholder="Optional notes for the audit record"
            onChange={(event) => onNotesChange(event.target.value)}
          />
        </label>
        <div className="packet-review-actions">
          <button type="submit" value="approved" disabled={!hasApplication || busy}>
            Approve packet
          </button>
          <button type="submit" value="changes_requested" className="secondary-button" disabled={!hasApplication || busy}>
            Request changes
          </button>
          <button type="submit" value="rejected" className="danger-button" disabled={!hasApplication || busy}>
            Reject packet
          </button>
        </div>
      </form>
      <div className="packet-review-history" aria-live="polite">
        {history.length ? (
          <>
            <div className="packet-review-history-heading">
              <strong>Packet review history</strong>
              <span>
                {history.length} recorded review{history.length === 1 ? "" : "s"}
              </span>
            </div>
            <div className="packet-review-history-list">
              {history.map((entry) => (
                <article className="compact-item packet-review-history-item" key={entry.id}>
                  <div className="stage-card-header">
                    <strong>{packetReviewLabel(entry.decision)}</strong>
                    <Badge value={entry.decision} />
                  </div>
                  <div className="meta">
                    Reviewed by {entry.reviewed_by} from {entry.source} on {formatDate(entry.created_at)}
                  </div>
                  <div className="meta">{entry.notes ? <strong>Notes: {entry.notes}</strong> : "No reviewer notes recorded."}</div>
                </article>
              ))}
            </div>
          </>
        ) : (
          <EmptyState title="No packet review history yet" detail="Record a human packet review decision to preserve manual approval evidence." />
        )}
      </div>
      <pre className="packet-preview">{packetText}</pre>
    </Panel>
  );
}
