import { RotateCcw, Search } from "lucide-react";

export function Toolbar({
  apiBase,
  applicationId,
  onApiBaseChange,
  onApplicationIdChange,
  onLoadAudit,
  onResetDemo,
  busy,
}: {
  apiBase: string;
  applicationId: string;
  onApiBaseChange: (value: string) => void;
  onApplicationIdChange: (value: string) => void;
  onLoadAudit: () => void;
  onResetDemo: () => void;
  busy: boolean;
}) {
  return (
    <section className="toolbar" aria-label="Audit dashboard controls" id="dashboard">
      <div className="toolbar-title">
        <div className="brand-lockup">
          <span className="brand-mark" aria-hidden="true" />
          <span className="wordmark">
            Apply<span>Go</span>
          </span>
        </div>
        <div>
          <p className="eyebrow">Governed workflow</p>
          <h1>Application audit dashboard</h1>
        </div>
      </div>
      <form
        className="controls"
        onSubmit={(event) => {
          event.preventDefault();
          onLoadAudit();
        }}
      >
        <label>
          <span>API base</span>
          <input type="url" value={apiBase} onChange={(event) => onApiBaseChange(event.target.value)} />
        </label>
        <label>
          <span>Application ID</span>
          <input
            type="text"
            placeholder="UUID from demo_seed output"
            value={applicationId}
            onChange={(event) => onApplicationIdChange(event.target.value)}
          />
        </label>
        <button type="submit" title="Load application audit evidence" disabled={busy}>
          <Search aria-hidden="true" size={16} />
          Load audit
        </button>
        <button type="button" className="secondary-button" onClick={onResetDemo} title="Reset to local demo data" disabled={busy}>
          <RotateCcw aria-hidden="true" size={16} />
          Reset demo
        </button>
      </form>
    </section>
  );
}
