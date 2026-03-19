"use client";

import { useQuery } from "@tanstack/react-query";
import { apiRoot } from "@/lib/api";
import type { DashboardStats } from "@/lib/types";

const DASHBOARD_QUERY_KEY = ["dashboard-stats"] as const;

async function fetchDashboardStats(): Promise<DashboardStats> {
  const { data } = await apiRoot.get<DashboardStats>("/api/dashboard/stats");
  return data;
}

export function useDashboard() {
  const {
    data: stats,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: DASHBOARD_QUERY_KEY,
    queryFn: fetchDashboardStats,
    staleTime: 60_000,
    retry: 1,
  });

  return { stats: stats ?? null, isLoading, error, refetch };
}
