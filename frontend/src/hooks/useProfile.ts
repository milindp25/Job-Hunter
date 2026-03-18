"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  UserWithProfile,
  ProfileUpdatePayload,
  PreferencesUpdatePayload,
  Skill,
  Education,
  Experience,
} from "@/lib/types";

const PROFILE_QUERY_KEY = ["user-profile"] as const;

async function fetchUserProfile(): Promise<UserWithProfile> {
  const { data } = await api.get<UserWithProfile>("/users/me");
  return data;
}

export function useProfile() {
  const queryClient = useQueryClient();

  const {
    data,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: PROFILE_QUERY_KEY,
    queryFn: fetchUserProfile,
  });

  const updateProfile = useMutation({
    mutationFn: async (payload: ProfileUpdatePayload) => {
      const { data } = await api.put<UserWithProfile>("/users/me/profile", payload);
      return data;
    },
    onSuccess: (updated) => {
      queryClient.setQueryData(PROFILE_QUERY_KEY, updated);
    },
  });

  const updateSkills = useMutation({
    mutationFn: async (skills: Skill[]) => {
      const { data } = await api.put<UserWithProfile>("/users/me/skills", { skills });
      return data;
    },
    onSuccess: (updated) => {
      queryClient.setQueryData(PROFILE_QUERY_KEY, updated);
    },
  });

  const updateExperience = useMutation({
    mutationFn: async (experience: Experience[]) => {
      const { data } = await api.put<UserWithProfile>("/users/me/experience", {
        experience,
      });
      return data;
    },
    onSuccess: (updated) => {
      queryClient.setQueryData(PROFILE_QUERY_KEY, updated);
    },
  });

  const updateEducation = useMutation({
    mutationFn: async (education: Education[]) => {
      const { data } = await api.put<UserWithProfile>("/users/me/education", {
        education,
      });
      return data;
    },
    onSuccess: (updated) => {
      queryClient.setQueryData(PROFILE_QUERY_KEY, updated);
    },
  });

  const updatePreferences = useMutation({
    mutationFn: async (payload: PreferencesUpdatePayload) => {
      const { data } = await api.put<UserWithProfile>("/users/me/preferences", payload);
      return data;
    },
    onSuccess: (updated) => {
      queryClient.setQueryData(PROFILE_QUERY_KEY, updated);
    },
  });

  return {
    user: data?.user ?? null,
    profile: data?.profile ?? null,
    isLoading,
    error,
    refetch,
    updateProfile,
    updateSkills,
    updateExperience,
    updateEducation,
    updatePreferences,
  };
}
