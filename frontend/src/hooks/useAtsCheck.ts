'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { AtsCheck, AtsCheckListResponse } from '@/lib/types';

const ATS_KEY = ['ats'] as const;

export function useAtsCheck(checkId: string | null) {
  const { data, isLoading, error } = useQuery({
    queryKey: [...ATS_KEY, 'detail', checkId],
    queryFn: async (): Promise<AtsCheck> => {
      const { data } = await api.get<AtsCheck>(`/ats/results/${checkId}`);
      return data;
    },
    enabled: !!checkId,
  });

  return { check: data ?? null, isLoading, error };
}

export function useAtsResults(resumeId?: string) {
  const searchParams = new URLSearchParams();
  if (resumeId) searchParams.set('resume_id', resumeId);
  const queryString = searchParams.toString();

  const { data, isLoading, error } = useQuery({
    queryKey: [...ATS_KEY, 'results', queryString],
    queryFn: async (): Promise<AtsCheckListResponse> => {
      const url = queryString ? `/ats/results?${queryString}` : '/ats/results';
      const { data } = await api.get<AtsCheckListResponse>(url);
      return data;
    },
  });

  return {
    checks: data?.checks ?? [],
    total: data?.total ?? 0,
    page: data?.page ?? 1,
    pageSize: data?.page_size ?? 20,
    isLoading,
    error,
  };
}

export function useRunAtsCheck() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (params: {
      resumeId: string;
      jobId?: string;
    }): Promise<AtsCheck> => {
      const { data } = await api.post<AtsCheck>('/ats/check', {
        resume_id: params.resumeId,
        job_id: params.jobId ?? null,
      });
      return data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ATS_KEY }),
  });
}

export function useDismissFinding() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (params: {
      checkId: string;
      findingId: string;
      dismissed: boolean;
    }): Promise<AtsCheck> => {
      const { data } = await api.patch<AtsCheck>(
        `/ats/results/${params.checkId}/findings/${params.findingId}/dismiss`,
        { dismissed: params.dismissed },
      );
      return data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ATS_KEY }),
  });
}
