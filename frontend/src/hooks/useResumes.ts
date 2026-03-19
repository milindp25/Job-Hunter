'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Resume, ResumeDownloadResponse, ResumeListResponse, ResumeUploadResponse } from '@/lib/types';

const RESUMES_KEY = ['resumes'] as const;

export function useResumes() {
  const queryClient = useQueryClient();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: RESUMES_KEY,
    queryFn: async (): Promise<ResumeListResponse> => {
      const { data } = await api.get<ResumeListResponse>('/resumes');
      return data;
    },
  });

  const uploadResume = useMutation({
    mutationFn: async (file: File): Promise<ResumeUploadResponse> => {
      const formData = new FormData();
      formData.append('file', file);
      const { data } = await api.post<ResumeUploadResponse>('/resumes', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: RESUMES_KEY }),
  });

  const deleteResume = useMutation({
    mutationFn: async (resumeId: string): Promise<void> => {
      await api.delete(`/resumes/${resumeId}`);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: RESUMES_KEY }),
  });

  const setPrimary = useMutation({
    mutationFn: async (resumeId: string): Promise<Resume> => {
      const { data } = await api.put<Resume>(`/resumes/${resumeId}/primary`);
      return data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: RESUMES_KEY }),
  });

  const getDownloadUrl = async (resumeId: string): Promise<string> => {
    const { data } = await api.get<ResumeDownloadResponse>(`/resumes/${resumeId}/download`);
    return data.download_url;
  };

  return {
    resumes: data?.resumes ?? [],
    total: data?.total ?? 0,
    isLoading,
    error,
    refetch,
    uploadResume,
    deleteResume,
    setPrimary,
    getDownloadUrl,
  };
}
