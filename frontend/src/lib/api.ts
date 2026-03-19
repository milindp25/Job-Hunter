import axios, {
  type AxiosError,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig,
} from "axios";
import {
  getAccessToken,
  refreshAccessToken,
  clearTokens,
} from "@/lib/auth";
import type {
  ApiError,
  DashboardStats,
  ResumeTemplatesResponse,
  TailoredResume,
  TailoredResumeListResponse,
} from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,
});

api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getAccessToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => Promise.reject(error),
);

let isRefreshing = false;
let refreshFailed = false;
let failedQueue: Array<{
  resolve: (token: string | null) => void;
  reject: (error: unknown) => void;
}> = [];

function processQueue(error: unknown, token: string | null): void {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error);
    } else {
      resolve(token);
    }
  });
  failedQueue = [];
}

/** Reset the refresh-failed flag (call after a successful login). */
export function resetRefreshState(): void {
  refreshFailed = false;
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiError>) => {
    const originalRequest = error.config as AxiosRequestConfig & {
      _retry?: boolean;
    };

    // Not a 401, or already retried, or refresh already failed this session
    if (error.response?.status !== 401 || originalRequest._retry || refreshFailed) {
      return Promise.reject(error);
    }

    if (isRefreshing) {
      return new Promise<string | null>((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      }).then((token) => {
        if (token && originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${token}`;
        }
        return api(originalRequest);
      });
    }

    originalRequest._retry = true;
    isRefreshing = true;

    try {
      const newToken = await refreshAccessToken();

      if (!newToken) {
        refreshFailed = true;
        clearTokens();
        processQueue(new Error("Refresh failed"), null);

        return Promise.reject(error);
      }

      processQueue(null, newToken);

      if (originalRequest.headers) {
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
      }

      return api(originalRequest);
    } catch (refreshError) {
      refreshFailed = true;
      processQueue(refreshError, null);
      clearTokens();
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  },
);

/**
 * Separate Axios instance for non-versioned API endpoints (health, dashboard).
 */
export const apiRoot = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

apiRoot.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getAccessToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => Promise.reject(error),
);

// ---------------------------------------------------------------------------
// Resume Generator API
// ---------------------------------------------------------------------------

export async function getResumeTemplates(): Promise<ResumeTemplatesResponse> {
  const { data } = await api.get<ResumeTemplatesResponse>("/resumes/templates");
  return data;
}

export async function generateResumePdf(
  resumeId: string,
  templateId: string,
  accentColor?: string,
): Promise<Blob> {
  const params = new URLSearchParams({ template: templateId });
  if (accentColor) {
    params.set("accent_color", accentColor);
  }
  const { data } = await api.get<Blob>(
    `/resumes/${resumeId}/generate?${params.toString()}`,
    { responseType: "blob" },
  );
  return data;
}

// ---------------------------------------------------------------------------
// Tailored Resume API
// ---------------------------------------------------------------------------

export async function tailorResume(
  resumeId: string,
  jobId: string,
): Promise<TailoredResume> {
  const { data } = await api.post<TailoredResume>("/tailored-resumes/", {
    resume_id: resumeId,
    job_id: jobId,
  });
  return data;
}

export async function getTailoredResume(
  id: string,
): Promise<TailoredResume> {
  const { data } = await api.get<TailoredResume>(`/tailored-resumes/${id}`);
  return data;
}

export async function listTailoredResumes(
  params?: { resume_id?: string; job_id?: string },
): Promise<TailoredResumeListResponse> {
  const { data } = await api.get<TailoredResumeListResponse>(
    "/tailored-resumes/",
    { params },
  );
  return data;
}

export async function deleteTailoredResume(id: string): Promise<void> {
  await api.delete(`/tailored-resumes/${id}`);
}

// ---------------------------------------------------------------------------
// Dashboard API
// ---------------------------------------------------------------------------

export async function getDashboardStats(): Promise<DashboardStats> {
  const { data } = await apiRoot.get<DashboardStats>("/api/dashboard/stats");
  return data;
}

export { api };
