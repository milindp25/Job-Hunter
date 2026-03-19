'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type {
  MatchResultsResponse,
  MatchAnalyzeResponse,
  SingleMatchAnalyzeResponse,
  JobMatchWithJob,
} from '@/lib/types';

const MATCHES_KEY = ['matches'] as const;

export function useMatchResults(
  params: { page?: number; pageSize?: number; minScore?: number } = {},
) {
  const searchParams = new URLSearchParams();

  if (params.page !== undefined) searchParams.set('page', String(params.page));
  if (params.pageSize !== undefined) searchParams.set('page_size', String(params.pageSize));
  if (params.minScore !== undefined) searchParams.set('min_score', String(params.minScore));

  const queryString = searchParams.toString();

  const { data, isLoading, error } = useQuery({
    queryKey: [...MATCHES_KEY, queryString],
    queryFn: async (): Promise<MatchResultsResponse> => {
      const url = queryString ? `/matching/results?${queryString}` : '/matching/results';
      const { data } = await api.get<MatchResultsResponse>(url);
      return data;
    },
  });

  return {
    matches: data?.matches ?? [],
    total: data?.total ?? 0,
    page: data?.page ?? 1,
    pageSize: data?.page_size ?? 20,
    isLoading,
    error,
  };
}

export function useTopMatches(limit: number = 5) {
  const { data, isLoading, error } = useQuery({
    queryKey: [...MATCHES_KEY, 'top', limit],
    queryFn: async (): Promise<MatchResultsResponse> => {
      const { data } = await api.get<MatchResultsResponse>(
        `/matching/results?page=1&page_size=${limit}&min_score=20`,
      );
      return data;
    },
  });

  return {
    matches: (data?.matches ?? []) as JobMatchWithJob[],
    total: data?.total ?? 0,
    isLoading,
    error,
  };
}

export function useMatchActions() {
  const queryClient = useQueryClient();

  const runBulkAnalysis = useMutation({
    mutationFn: async (): Promise<MatchAnalyzeResponse> => {
      const { data } = await api.post<MatchAnalyzeResponse>('/matching/analyze');
      return data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: MATCHES_KEY }),
  });

  const analyzeJob = useMutation({
    mutationFn: async (jobId: string): Promise<SingleMatchAnalyzeResponse> => {
      const { data } = await api.post<SingleMatchAnalyzeResponse>(
        `/matching/analyze/${jobId}`,
      );
      return data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: MATCHES_KEY }),
  });

  return { runBulkAnalysis, analyzeJob };
}
