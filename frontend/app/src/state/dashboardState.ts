import type { RecentApplicationFilters } from "../api/types";
import { inferApiBaseFromLocation, normalizeApiBase } from "../domain/apiBase";
import { DEFAULT_RECENT_FILTERS } from "../domain/recentFilters";

export type StatusTone = "" | "success" | "error" | "loading";

export interface DashboardStatus {
  tone: StatusTone;
  label: string;
  message: string;
}

export interface DashboardState {
  apiBase: string;
  applicationId: string;
  recentFilters: RecentApplicationFilters;
  recentEnabled: boolean;
  status: DashboardStatus;
  packetReviewNotes: string;
}

export type DashboardAction =
  | { type: "setApiBase"; value: string }
  | { type: "setApplicationId"; value: string }
  | { type: "setRecentFilters"; value: RecentApplicationFilters }
  | { type: "setRecentEnabled"; value: boolean }
  | { type: "setStatus"; value: DashboardStatus }
  | { type: "setPacketReviewNotes"; value: string }
  | { type: "resetDemo"; apiBase: string };

export function initialDashboardState(location: Location): DashboardState {
  return {
    apiBase: normalizeApiBase(inferApiBaseFromLocation(location) || "http://localhost:8000"),
    applicationId: "",
    recentFilters: DEFAULT_RECENT_FILTERS,
    recentEnabled: false,
    packetReviewNotes: "",
    status: {
      tone: "",
      label: "Demo mode",
      message: "Using local demo data until a backend application ID is provided.",
    },
  };
}

export function dashboardReducer(state: DashboardState, action: DashboardAction): DashboardState {
  switch (action.type) {
    case "setApiBase":
      return { ...state, apiBase: normalizeApiBase(action.value) };
    case "setApplicationId":
      return { ...state, applicationId: action.value.trim() };
    case "setRecentFilters":
      return { ...state, recentFilters: action.value };
    case "setRecentEnabled":
      return { ...state, recentEnabled: action.value };
    case "setStatus":
      return { ...state, status: action.value };
    case "setPacketReviewNotes":
      return { ...state, packetReviewNotes: action.value };
    case "resetDemo":
      return {
        ...state,
        apiBase: normalizeApiBase(action.apiBase),
        applicationId: "",
        recentFilters: DEFAULT_RECENT_FILTERS,
        recentEnabled: false,
        packetReviewNotes: "",
        status: {
          tone: "",
          label: "Demo reset",
          message: "Dashboard restored to the sample review baseline.",
        },
      };
    default:
      return state;
  }
}
