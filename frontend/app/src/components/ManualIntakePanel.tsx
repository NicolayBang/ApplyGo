import { ClipboardPlus } from "lucide-react";
import type { JobCreate } from "../api/types";
import { Panel, SectionHeading } from "./ui";
import { sampleJob } from "../domain/sampleJob";

export interface IntakeFormState {
  title: string;
  company: string;
  location: string;
  sourceUrl: string;
  remoteOk: boolean;
  rawText: string;
}

export const blankIntakeForm: IntakeFormState = {
  title: "",
  company: "",
  location: "",
  sourceUrl: "",
  remoteOk: true,
  rawText: "",
};

export function intakeToJobCreate(form: IntakeFormState): JobCreate {
  return {
    title: form.title.trim(),
    company: form.company.trim(),
    location: form.location.trim() || null,
    source_url: form.sourceUrl.trim() || null,
    raw_text: form.rawText.trim() || null,
    remote_ok: form.remoteOk,
  };
}

export function ManualIntakePanel({
  form,
  isCreating,
  disabled,
  onChange,
  onCreate,
  onSample,
}: {
  form: IntakeFormState;
  isCreating: boolean;
  disabled: boolean;
  onChange: (form: IntakeFormState) => void;
  onCreate: () => void;
  onSample: () => void;
}) {
  return (
    <Panel id="manual-intake" className="intake-panel" label="Manual job intake">
      <SectionHeading title="Manual intake" meta="Create application" />
      <form
        className="intake-form"
        onSubmit={(event) => {
          event.preventDefault();
          onCreate();
        }}
      >
        <label>
          <span>Role title</span>
          <input
            required
            value={form.title}
            placeholder={sampleJob.title ?? ""}
            onChange={(event) => onChange({ ...form, title: event.target.value })}
          />
        </label>
        <label>
          <span>Company</span>
          <input
            required
            value={form.company}
            placeholder={sampleJob.company ?? ""}
            onChange={(event) => onChange({ ...form, company: event.target.value })}
          />
        </label>
        <label>
          <span>Location</span>
          <input
            value={form.location}
            placeholder={sampleJob.location ?? ""}
            onChange={(event) => onChange({ ...form, location: event.target.value })}
          />
        </label>
        <label>
          <span>Job URL</span>
          <input
            type="url"
            value={form.sourceUrl}
            placeholder={sampleJob.source_url ?? ""}
            onChange={(event) => onChange({ ...form, sourceUrl: event.target.value })}
          />
        </label>
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={form.remoteOk}
            onChange={(event) => onChange({ ...form, remoteOk: event.target.checked })}
          />
          <span>Remote ok</span>
        </label>
        <button type="submit" disabled={disabled}>
          <ClipboardPlus aria-hidden="true" size={16} />
          {isCreating ? "Creating" : "Create"}
        </button>
        <button type="button" className="secondary-button" onClick={onSample}>
          Sample job
        </button>
        <label className="job-description-field">
          <span>Job description</span>
          <textarea
            value={form.rawText}
            placeholder="Paste the job post or key requirements"
            rows={6}
            onChange={(event) => onChange({ ...form, rawText: event.target.value })}
          />
        </label>
      </form>
    </Panel>
  );
}
