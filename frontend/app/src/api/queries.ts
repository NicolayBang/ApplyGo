import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "./client";
import type {
  ApplicationPacketReviewCreate,
  ApplicationStateUpdate,
  DashboardData,
  ExecutorDryRunRequest,
  JobCreate,
  PolicyEvaluationRequest,
  RecentApplicationFilters,
} from "./types";
import { isValidUuid } from "../domain/workflow";

export const queryKeys = {
  audit: (apiBase: string, applicationId: string) => ["audit", apiBase, applicationId] as const,
  reviewSummary: (apiBase: string, applicationId: string) => ["review-summary", apiBase, applicationId] as const,
  dashboard: (apiBase: string, applicationId: string) => ["dashboard", apiBase, applicationId] as const,
  recent: (apiBase: string, filters: RecentApplicationFilters) => ["recent", apiBase, filters] as const,
};

export function useDashboardQuery(apiBase: string, applicationId: string) {
  return useQuery({
    queryKey: queryKeys.dashboard(apiBase, applicationId),
    enabled: Boolean(apiBase && isValidUuid(applicationId)),
    retry: false,
    queryFn: async (): Promise<DashboardData> => {
      const client = apiClient(apiBase);
      const [audit, reviewSummary] = await Promise.all([
        client.getAudit(applicationId),
        client.getReviewSummary(applicationId),
      ]);
      return { audit, reviewSummary };
    },
  });
}

export function useRecentApplicationsQuery(apiBase: string, filters: RecentApplicationFilters, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.recent(apiBase, filters),
    enabled: Boolean(apiBase && enabled),
    retry: false,
    queryFn: () => apiClient(apiBase).listApplications(filters),
  });
}

export function useDashboardMutations(apiBase: string, applicationId: string) {
  const queryClient = useQueryClient();

  const invalidateDashboard = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard(apiBase, applicationId) }),
      queryClient.invalidateQueries({ queryKey: ["recent", apiBase] }),
    ]);
  };

  return {
    createManualApplication: useMutation({
      mutationFn: async (job: JobCreate) => {
        const client = apiClient(apiBase);
        const createdJob = await client.createJob(job);
        return client.createApplication(createdJob.id);
      },
      onSuccess: async (application) => {
        await queryClient.invalidateQueries({ queryKey: ["recent", apiBase] });
        return application;
      },
    }),
    scoreApplication: useMutation({
      mutationFn: () => apiClient(apiBase).scoreApplication(applicationId, { actor: "user" }),
      onSuccess: invalidateDashboard,
    }),
    transitionState: useMutation({
      mutationFn: (payload: ApplicationStateUpdate) =>
        apiClient(apiBase).updateApplicationState(applicationId, payload),
      onSuccess: invalidateDashboard,
    }),
    evaluatePolicy: useMutation({
      mutationFn: (payload: PolicyEvaluationRequest) => apiClient(apiBase).evaluatePolicy(applicationId, payload),
      onSuccess: invalidateDashboard,
    }),
    dryRun: useMutation({
      mutationFn: (payload: ExecutorDryRunRequest) => apiClient(apiBase).dryRunExecutor(applicationId, payload),
      onSuccess: invalidateDashboard,
    }),
    recordPacketReview: useMutation({
      mutationFn: (payload: ApplicationPacketReviewCreate) => apiClient(apiBase).recordPacketReview(applicationId, payload),
      onSuccess: invalidateDashboard,
    }),
  };
}
