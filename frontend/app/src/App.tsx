import { useEffect, useMemo, useReducer, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import type { ApplicationState, PacketReviewDecision, RecentApplicationFilters } from "./api/types";
import { queryKeys, useDashboardMutations, useDashboardQuery, useRecentApplicationsQuery } from "./api/queries";
import { AuditTimeline } from "./components/AuditTimeline";
import { EvidenceGrid } from "./components/EvidenceGrid";
import {
  blankIntakeForm,
  intakeToJobCreate,
  ManualIntakePanel,
  type IntakeFormState,
} from "./components/ManualIntakePanel";
import { NextActionCard, LifecycleStepper } from "./components/Overview";
import { PacketPanel } from "./components/PacketPanel";
import { RecentApplicationsPanel } from "./components/RecentApplicationsPanel";
import { ReviewReadiness } from "./components/ReviewReadiness";
import { Sidebar } from "./components/Sidebar";
import { StatusRow } from "./components/StatusRow";
import { Toolbar } from "./components/Toolbar";
import { WorkflowActions } from "./components/WorkflowActions";
import { demoAudit, demoReviewSummary } from "./domain/demoData";
import { sampleJob } from "./domain/sampleJob";
import {
  dryRunBlockReason,
  isValidUuid,
  latestAllowedPolicyDecision,
  policyContextFromApplication,
} from "./domain/workflow";
import { dashboardReducer, initialDashboardState } from "./state/dashboardState";

function useDebouncedValue<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(value), delay);
    return () => window.clearTimeout(timer);
  }, [delay, value]);

  return debounced;
}

function sampleIntakeForm(): IntakeFormState {
  return {
    title: sampleJob.title ?? "",
    company: sampleJob.company ?? "",
    location: sampleJob.location ?? "",
    sourceUrl: sampleJob.source_url ?? "",
    remoteOk: sampleJob.remote_ok,
    rawText: sampleJob.raw_text ?? "",
  };
}

function downloadTextFile(fileName: string, text: string) {
  const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}

export function App() {
  const [state, dispatch] = useReducer(dashboardReducer, window.location, initialDashboardState);
  const [intakeForm, setIntakeForm] = useState<IntakeFormState>(sampleIntakeForm);
  const debouncedFilters = useDebouncedValue(state.recentFilters, 300);
  const queryClient = useQueryClient();
  const dashboardQuery = useDashboardQuery(state.apiBase, state.applicationId);
  const recentQuery = useRecentApplicationsQuery(state.apiBase, debouncedFilters, state.recentEnabled);
  const mutations = useDashboardMutations(state.apiBase, state.applicationId);

  const liveData = dashboardQuery.data;
  const audit = liveData?.audit ?? demoAudit;
  const reviewSummary = liveData?.reviewSummary ?? demoReviewSummary;
  const busy =
    dashboardQuery.isFetching ||
    mutations.createManualApplication.isPending ||
    mutations.scoreApplication.isPending ||
    mutations.transitionState.isPending ||
    mutations.evaluatePolicy.isPending ||
    mutations.dryRun.isPending ||
    mutations.recordPacketReview.isPending;

  useEffect(() => {
    if (!state.applicationId) return;
    if (!isValidUuid(state.applicationId)) {
      dispatch({
        type: "setStatus",
        value: {
          tone: "error",
          label: "Invalid ID",
          message: "Application ID must be a valid UUID.",
        },
      });
    }
  }, [state.applicationId]);

  useEffect(() => {
    if (dashboardQuery.isSuccess) {
      dispatch({
        type: "setStatus",
        value: {
          tone: "",
          label: "Live data",
          message: "Audit summary loaded from the backend.",
        },
      });
    }
  }, [dashboardQuery.isSuccess, dashboardQuery.dataUpdatedAt]);

  useEffect(() => {
    if (dashboardQuery.isError) {
      const message = dashboardQuery.error instanceof Error ? dashboardQuery.error.message : "Unable to load audit.";
      dispatch({
        type: "setStatus",
        value: {
          tone: "error",
          label: "Fallback",
          message: `${message} Showing demo data for review.`,
        },
      });
    }
  }, [dashboardQuery.isError, dashboardQuery.error]);

  useEffect(() => {
    if (recentQuery.isError) {
      const message = recentQuery.error instanceof Error ? recentQuery.error.message : "Unable to load recent applications.";
      dispatch({
        type: "setStatus",
        value: {
          tone: "error",
          label: "Recent failed",
          message,
        },
      });
    }
  }, [recentQuery.isError, recentQuery.error]);

  const recentApplications = useMemo(() => recentQuery.data ?? [], [recentQuery.data]);

  const setStatus = (label: string, message: string, tone: "" | "success" | "error" | "loading" = "") => {
    dispatch({ type: "setStatus", value: { label, message, tone } });
  };

  const loadAudit = async () => {
    if (!state.applicationId) {
      await queryClient.cancelQueries({ queryKey: queryKeys.dashboard(state.apiBase, state.applicationId) });
      setStatus("Demo mode", "Using local demo data until a backend application ID is provided.");
      return;
    }

    if (!isValidUuid(state.applicationId)) {
      setStatus("Invalid ID", "Application ID must be a valid UUID.", "error");
      return;
    }

    setStatus("Loading", "Fetching audit summary from the backend.", "loading");
    await dashboardQuery.refetch();
  };

  const createManualApplication = async () => {
    const job = intakeToJobCreate(intakeForm);
    if (!job.title || !job.company) {
      setStatus("Missing info", "Role title and company are required.", "error");
      return;
    }

    try {
      setStatus("Creating", "Creating job and application records.", "loading");
      const application = await mutations.createManualApplication.mutateAsync(job);
      dispatch({ type: "setApplicationId", value: application.id });
      dispatch({ type: "setRecentEnabled", value: true });
      setStatus("Created", "Manual application created and audit trail loaded.");
    } catch (error) {
      setStatus("Create failed", error instanceof Error ? error.message : "Application creation failed.", "error");
    }
  };

  const transitionApplicationState = async (targetState: ApplicationState, destructive: boolean) => {
    if (destructive && !window.confirm(`Confirm ${targetState}. This records an audited workflow state change.`)) {
      return;
    }

    try {
      setStatus("State", `Moving application to ${targetState}.`, "loading");
      await mutations.transitionState.mutateAsync({
        state: targetState,
        actor: "user",
        payload: {
          source: "dashboard",
          previous_state: audit.application.state,
        },
      });
      setStatus("State updated", `Application moved to ${targetState}.`);
    } catch (error) {
      setStatus("State failed", error instanceof Error ? error.message : "State transition failed.", "error");
    }
  };

  const scoreApplication = async () => {
    try {
      setStatus("Scoring", "Scoring application using deterministic job data.", "loading");
      await mutations.scoreApplication.mutateAsync();
      setStatus("Scored", "Application score recorded in the audit trail.");
    } catch (error) {
      setStatus("Score failed", error instanceof Error ? error.message : "Scoring failed.", "error");
    }
  };

  const evaluatePolicy = async () => {
    const context = policyContextFromApplication(audit.application);
    if (!context) {
      setStatus("Score needed", "Score the application before evaluating policy.", "error");
      return;
    }

    try {
      setStatus("Policy", "Evaluating dry-run follow-up policy.", "loading");
      await mutations.evaluatePolicy.mutateAsync({
        requested_action: "send_follow_up_email",
        worker: "email",
        mode: "dry_run",
        context,
      });
      setStatus("Policy logged", "Policy decision recorded in the audit trail.");
    } catch (error) {
      setStatus("Policy failed", error instanceof Error ? error.message : "Policy evaluation failed.", "error");
    }
  };

  const dryRunFollowUp = async () => {
    const decision = latestAllowedPolicyDecision(audit);
    if (!decision) {
      setStatus("Policy needed", dryRunBlockReason(null), "error");
      return;
    }

    try {
      setStatus("Dry run", "Planning follow-up action with the executor stub.", "loading");
      await mutations.dryRun.mutateAsync({
        policy_decision_id: decision.id,
        action_type: "send_follow_up_email",
        idempotency_key: `dashboard-follow-up-${state.applicationId}`,
        payload: {
          source: "dashboard",
          template: "manual_follow_up",
        },
      });
      setStatus("Dry-run logged", "Executor dry-run result recorded in the audit trail.");
    } catch (error) {
      setStatus("Dry-run failed", error instanceof Error ? error.message : "Dry-run failed.", "error");
    }
  };

  const recordPacketReview = async (decision: PacketReviewDecision) => {
    if (decision === "rejected" && !window.confirm("Reject this packet? The review decision is recorded for audit.")) {
      return;
    }

    try {
      setStatus("Review", "Recording human packet review decision.", "loading");
      await mutations.recordPacketReview.mutateAsync({
        decision,
        reviewed_by: "human",
        source: "dashboard",
        notes: state.packetReviewNotes.trim() || null,
      });
      dispatch({ type: "setPacketReviewNotes", value: "" });
      setStatus("Review recorded", "Packet review recorded. No email, browser action, or submission occurred.", "success");
    } catch (error) {
      setStatus("Review failed", error instanceof Error ? error.message : "Packet review failed.", "error");
    }
  };

  const copyText = async (text: string, successMessage: string) => {
    if (!navigator.clipboard?.writeText) {
      setStatus("Copy unavailable", "Clipboard access is not available in this browser.", "error");
      return;
    }

    try {
      await navigator.clipboard.writeText(text);
      setStatus("Copied", successMessage, "success");
    } catch {
      setStatus("Copy unavailable", "Clipboard permission was denied by the browser.", "error");
    }
  };

  const updateRecentFilters = (filters: RecentApplicationFilters) => {
    dispatch({ type: "setRecentFilters", value: filters });
    if (state.recentEnabled) {
      setStatus("Loading", "Fetching recent applications from the backend.", "loading");
    }
  };

  return (
    <main className="shell">
      <Sidebar />
      <Toolbar
        apiBase={state.apiBase}
        applicationId={state.applicationId}
        onApiBaseChange={(value) => dispatch({ type: "setApiBase", value })}
        onApplicationIdChange={(value) => dispatch({ type: "setApplicationId", value })}
        onLoadAudit={loadAudit}
        onResetDemo={() => {
          setIntakeForm(sampleIntakeForm());
          dispatch({ type: "resetDemo", apiBase: state.apiBase });
        }}
      />
      <StatusRow status={state.status} />
      <section className="guided-overview" aria-label="Guided workflow overview">
        <NextActionCard applicationId={state.applicationId} audit={audit} reviewSummary={reviewSummary} />
        <LifecycleStepper audit={audit} />
      </section>
      <RecentApplicationsPanel
        applications={recentApplications}
        filters={state.recentFilters}
        isLoading={recentQuery.isFetching}
        onFiltersChange={updateRecentFilters}
        onLoad={() => {
          dispatch({ type: "setRecentEnabled", value: true });
          setStatus("Loading", "Fetching recent applications from the backend.", "loading");
          void recentQuery.refetch();
        }}
        onSelect={(applicationId) => {
          dispatch({ type: "setApplicationId", value: applicationId });
          setStatus("Loading", "Fetching audit summary from the backend.", "loading");
        }}
      />
      <ManualIntakePanel
        form={intakeForm}
        isCreating={mutations.createManualApplication.isPending}
        onChange={setIntakeForm}
        onCreate={createManualApplication}
        onSample={() => {
          setIntakeForm(sampleIntakeForm());
          setStatus("Sample loaded", "Review the sample job, then create the application.");
        }}
      />
      <WorkflowActions
        applicationId={state.applicationId}
        audit={audit}
        reviewSummary={reviewSummary}
        busy={busy}
        onScore={scoreApplication}
        onPolicy={evaluatePolicy}
        onDryRun={dryRunFollowUp}
        onTransition={transitionApplicationState}
      />
      <ReviewReadiness summary={reviewSummary} />
      <EvidenceGrid audit={audit} />
      <PacketPanel
        applicationId={state.applicationId}
        audit={audit}
        reviewSummary={reviewSummary}
        notes={state.packetReviewNotes}
        busy={busy}
        onNotesChange={(value) => dispatch({ type: "setPacketReviewNotes", value })}
        onCopy={copyText}
        onDownload={(fileName, text) => {
          downloadTextFile(fileName, text);
          setStatus("Packet downloaded", "Application packet preview downloaded as a text file.", "success");
        }}
        onReview={recordPacketReview}
      />
      <AuditTimeline events={audit.events} />
    </main>
  );
}
