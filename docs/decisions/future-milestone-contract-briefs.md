# Future Milestone Contract Briefs

**Status:** Review briefs only

**Milestones:** M5-M9

**Does not authorize implementation:** Yes

These briefs preserve the decisions that must be made before later milestones. They intentionally
avoid implementation-ready schemas, provider payloads, and workflow values until the owning
milestone is active.

## M5 Packet And Answer Brief

### Intended capability

Generate and store reviewable application packets containing document drafts, immutable rendered
versions, attachments, and screening answers.

### Decisions required

- logical document identity versus immutable version identity;
- application-to-version roles and reuse across applications;
- content, artifact URI, checksum, format, provenance, and generator version;
- answer ownership, sensitivity, approval, reuse, and supersession;
- retention and deletion after a version has been used;
- packet readiness, review, approval, and failure evidence.

### Entry gate

Approve the lifecycle model, privacy/retention policy, M5 schema contract, migration/compatibility
contract, and document-worker action schemas.

## M6 Review Workflow Brief

### Intended capability

Provide a human review queue for packet, policy, submission, and communication decisions with
auditable approvals and overrides.

### Decisions required

- queue membership and priority;
- reviewer identity and authorization;
- approval, rejection, return-for-edit, and override records;
- override scope, reason, expiry, and revocation;
- stale evidence and concurrent review behavior;
- API/dashboard compatibility and event vocabulary.

### Entry gate

Approve the lifecycle contract and a human approval/override contract. An override must never edit
or erase the policy decision it responds to.

## M7 Recruiter Communication Brief

### Intended capability

Synchronize recruiter messages, classify inbound communication, update tracker evidence, and draft
replies that remain behind policy and human-review gates.

### Decisions required

- contact, thread, message, and application relationship ownership;
- provider IDs, synchronization cursors, duplicate delivery, and replay;
- immutable raw content versus editable drafts;
- sender, recipient, attachment, and timestamp representation;
- conversation states and lifecycle signal confidence;
- draft versus send action schemas;
- privacy, retention, redaction, consent, and access.

### Entry gate

Approve communication schema, provider-sync, privacy/retention, executor hardening, lifecycle, and
human override contracts. Unknown or low-confidence signals must route to review.

## M8 Browser Execution Brief

### Intended capability

Fill supported application forms and upload approved artifacts while preserving dry-run parity,
pause-before-submit behavior, and auditable fallback.

### Decisions required

- supported ATS/domain/template allowlist;
- structured browser action and dry-run plan schemas;
- field provenance and approved answer sources;
- artifact selection and upload evidence;
- page-change detection, timeout, retry, and idempotency behavior;
- captcha, login, unknown field, legal/disclosure, salary, and conflicting-data fallback;
- screenshot or trace evidence and sensitive-data handling;
- human pause, resume, cancel, and manual-completion report.

### Entry gate

Approve executor hardening, browser action, credential boundary, privacy, supported-template, and
submission transition contracts. Captcha bypass and anti-bot evasion remain prohibited.

## M9 Full-Auto Guardrails Brief

### Intended capability

Allow narrowly scoped automatic submission only when the same governed workflow can prove that all
policy, confidence, domain, template, rate, and safety conditions are satisfied.

### Decisions required

- trusted-domain and ATS-template allowlists;
- minimum fit/confidence thresholds and prohibited question categories;
- per-day, per-company, per-domain, and global limits;
- deterministic rate-limit keys and distributed enforcement;
- global and scoped kill switches;
- monitoring, alerting, reconciliation, and audit review;
- fallback to semi-auto for any unknown, conflicting, blocked, or low-confidence condition;
- incident handling and authority to disable automation.

### Entry gate

M7 and M8 must first demonstrate audited dry-run and execute behavior. Approve rate-limit,
kill-switch, monitoring, incident, human override, and full-auto policy contracts with runnable
failure and shutdown tests.

## Shared Boundary

For every milestone:

- workflow remains the only state owner;
- database remains the durable source of truth;
- policy remains the only permission owner;
- LLM output is evidence or draft content, never permission or state authority;
- workers execute only structured, approved executor actions;
- policy and execution evidence are logged before state updates;
- dry-run and human fallback remain available;
- the implementation PR must link an approved milestone contract and update the contract registry.
