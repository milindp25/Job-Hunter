"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  tailorResume,
  getTailoredResume,
  listTailoredResumes,
  deleteTailoredResume,
} from "@/lib/api";

const TAILORED_RESUMES_KEY = ["tailored-resumes"] as const;

export function useTailorResume() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ resumeId, jobId }: { resumeId: string; jobId: string }) =>
      tailorResume(resumeId, jobId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: TAILORED_RESUMES_KEY });
    },
  });
}

export function useTailoredResume(id: string | null) {
  return useQuery({
    queryKey: [...TAILORED_RESUMES_KEY, id],
    queryFn: () => getTailoredResume(id!),
    enabled: id !== null,
  });
}

export function useTailoredResumeList(params?: {
  resume_id?: string;
  job_id?: string;
}) {
  return useQuery({
    queryKey: [...TAILORED_RESUMES_KEY, "list", params],
    queryFn: () => listTailoredResumes(params),
  });
}

export function useDeleteTailoredResume() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteTailoredResume(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: TAILORED_RESUMES_KEY });
    },
  });
}
