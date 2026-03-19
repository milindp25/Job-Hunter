"use client";

import { Bookmark, Target, FileText, Shield } from "lucide-react";
import type { DashboardStats } from "@/lib/types";

interface StatCardProps {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  accent: string;
}

function StatCard({ label, value, icon, accent }: StatCardProps) {
  return (
    <div className="rounded-xl border border-foreground/10 bg-background p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-foreground/60">{label}</p>
        <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${accent}`}>
          {icon}
        </div>
      </div>
      <p className="mt-3 text-3xl font-bold text-foreground">{value}</p>
    </div>
  );
}

interface StatsGridProps {
  stats: DashboardStats | null;
}

export function StatsGrid({ stats }: StatsGridProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <StatCard
        label="Saved Jobs"
        value={stats?.total_saved_jobs ?? 0}
        icon={<Bookmark className="h-5 w-5 text-blue-600" />}
        accent="bg-blue-100 dark:bg-blue-900/30"
      />
      <StatCard
        label="Total Matches"
        value={stats?.total_matches ?? 0}
        icon={<Target className="h-5 w-5 text-green-600" />}
        accent="bg-green-100 dark:bg-green-900/30"
      />
      <StatCard
        label="Resumes"
        value={stats?.resumes_count ?? 0}
        icon={<FileText className="h-5 w-5 text-purple-600" />}
        accent="bg-purple-100 dark:bg-purple-900/30"
      />
      <StatCard
        label="Avg ATS Score"
        value={stats?.avg_ats_score != null ? `${stats.avg_ats_score}%` : "N/A"}
        icon={<Shield className="h-5 w-5 text-orange-600" />}
        accent="bg-orange-100 dark:bg-orange-900/30"
      />
    </div>
  );
}
