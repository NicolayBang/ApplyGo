import type { JobCreate } from "../api/types";

export const sampleJob: Required<Pick<JobCreate, "title" | "company" | "location" | "source_url" | "remote_ok" | "raw_text">> = {
  title: "Backend Platform Engineer",
  company: "ApplyGo Demo Co.",
  location: "Remote",
  source_url: "https://jobs.lever.co/applygo/backend-platform-engineer",
  remote_ok: true,
  raw_text:
    "Build Python APIs with FastAPI, PostgreSQL, automation workflows, and platform data services. This is a full-time remote role with a salary range of $95,000 - $125,000. Partner with DevOps and product teams to improve reliable backend delivery.",
};
