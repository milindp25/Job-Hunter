'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type {
  JobListResponse,
  JobSearchParams,
  SavedJobListResponse,
  JobFetchResponse,
} from '@/lib/types';

const JOBS_KEY = ['jobs'] as const;
const SAVED_JOBS_KEY = ['saved-jobs'] as const;

export function useJobs(params: JobSearchParams = {}) {
  const searchParams = new URLSearchParams();

  if (params.query) searchParams.set('query', params.query);
  if (params.location) searchParams.set('location', params.location);
  if (params.salary_min !== undefined) searchParams.set('salary_min', String(params.salary_min));
  if (params.salary_max !== undefined) searchParams.set('salary_max', String(params.salary_max));
  if (params.job_type) searchParams.set('job_type', params.job_type);
  if (params.source) searchParams.set('source', params.source);
  if (params.is_remote !== undefined) searchParams.set('is_remote', String(params.is_remote));
  if (params.page !== undefined) searchParams.set('page', String(params.page));
  if (params.page_size !== undefined) searchParams.set('page_size', String(params.page_size));

  const queryString = searchParams.toString();

  const { data, isLoading, error } = useQuery({
    queryKey: [...JOBS_KEY, queryString],
    queryFn: async (): Promise<JobListResponse> => {
      const url = queryString ? `/jobs?${queryString}` : '/jobs';
      const { data } = await api.get<JobListResponse>(url);
      return data;
    },
  });

  return {
    jobs: data?.jobs ?? [],
    total: data?.total ?? 0,
    page: data?.page ?? 1,
    pageSize: data?.page_size ?? 20,
    isLoading,
    error,
  };
}

export function useSavedJobs() {
  const { data, isLoading, error } = useQuery({
    queryKey: SAVED_JOBS_KEY,
    queryFn: async (): Promise<SavedJobListResponse> => {
      const { data } = await api.get<SavedJobListResponse>('/jobs/saved');
      return data;
    },
  });

  return {
    savedJobs: data?.saved_jobs ?? [],
    total: data?.total ?? 0,
    isLoading,
    error,
  };
}

export function useJobActions() {
  const queryClient = useQueryClient();

  const saveJob = useMutation({
    mutationFn: async (jobId: string): Promise<void> => {
      await api.post(`/jobs/${jobId}/save`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: JOBS_KEY });
      queryClient.invalidateQueries({ queryKey: SAVED_JOBS_KEY });
    },
  });

  const unsaveJob = useMutation({
    mutationFn: async (jobId: string): Promise<void> => {
      await api.delete(`/jobs/${jobId}/save`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: JOBS_KEY });
      queryClient.invalidateQueries({ queryKey: SAVED_JOBS_KEY });
    },
  });

  const fetchJobs = useMutation({
    mutationFn: async (): Promise<JobFetchResponse> => {
      const { data } = await api.post<JobFetchResponse>('/jobs/fetch');
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: JOBS_KEY });
    },
  });

  return { saveJob, unsaveJob, fetchJobs };
}
