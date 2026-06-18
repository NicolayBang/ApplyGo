import type { ApplicationAuditRead, ApplicationReviewSummaryRead } from "../api/types";
import { Badge, Panel, SectionHeading } from "./ui";
import { displayLabel } from "../domain/labels";
import { lifecycleSteps, nextAction } from "../domain/workflow";

export function NextActionCard({
  applicationId,
  audit,
  reviewSummary,
}: {
  applicationId: string;
  audit: ApplicationAuditRead;
  reviewSummary: ApplicationReviewSummaryRead;
}) {
  const action = nextAction(applicationId, audit, reviewSummary);

  return (
    <Panel className="next-action-panel">
      <SectionHeading title="Next action" meta={action.status} />
      <strong>{action.title}</strong>
      <p>{action.detail}</p>
    </Panel>
  );
}

export function LifecycleStepper({ audit }: { audit: ApplicationAuditRead }) {
  const currentIndex = lifecycleSteps.findIndex((step) => step.state === audit.application.state);

  return (
    <Panel className="lifecycle-panel">
      <SectionHeading title="Application progress" meta="Existing states only" />
      <ol className="lifecycle-stepper">
        {lifecycleSteps.map((step, index) => {
          const classes = ["lifecycle-step"];
          if (index === currentIndex) classes.push("active");
          if (currentIndex > index) classes.push("complete");

          return (
            <li className={classes.join(" ")} key={step.state}>
              <span className="step-dot" aria-hidden="true" />
              <span>{step.label}</span>
            </li>
          );
        })}
      </ol>
      <div className="lifecycle-state">
        <span>Current state</span>
        <Badge value={displayLabel(audit.application.state)} />
      </div>
    </Panel>
  );
}
