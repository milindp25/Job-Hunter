"use client";

import { User, Search, FileCheck, AlertCircle } from "lucide-react";
import { useProfile } from "@/hooks/useProfile";
import { ProfileCompletenessCard } from "./profile-completeness-card";
import { TopMatchesCard } from "./top-matches-card";
import { QuickActionCard } from "./quick-action-card";

function DashboardSkeleton() {
  return (
    <div className="space-y-8" role="status">
      <div className="h-8 w-64 animate-pulse rounded-lg bg-foreground/10" />
      <div className="h-24 w-full animate-pulse rounded-xl bg-foreground/10" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div className="h-36 animate-pulse rounded-xl bg-foreground/10" />
        <div className="h-36 animate-pulse rounded-xl bg-foreground/10" />
        <div className="h-36 animate-pulse rounded-xl bg-foreground/10" />
      </div>
      <span className="sr-only">Loading dashboard...</span>
    </div>
  );
}

export function DashboardContent() {
  const { user, profile, isLoading } = useProfile();

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  const completeness = profile?.profile_completeness ?? 0;
  const showEmptyState = completeness < 30;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground">
          Welcome back, {user?.full_name ?? "there"}!
        </h1>
        <p className="mt-1 text-foreground/60">
          Here&apos;s an overview of your job hunting progress.
        </p>
      </div>

      <ProfileCompletenessCard completeness={completeness} />

      <TopMatchesCard />

      {showEmptyState && (
        <div className="flex items-start gap-4 rounded-xl border border-yellow-200 bg-yellow-50 p-5 dark:border-yellow-900 dark:bg-yellow-950">
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-yellow-600 dark:text-yellow-400" />
          <div>
            <h3 className="text-sm font-semibold text-yellow-800 dark:text-yellow-200">
              Complete your profile to get started
            </h3>
            <p className="mt-1 text-sm text-yellow-700 dark:text-yellow-300">
              Fill in your skills, experience, and preferences so we can match
              you with the best job opportunities.
            </p>
          </div>
        </div>
      )}

      <div>
        <h2 className="mb-4 text-lg font-semibold text-foreground">
          Quick Actions
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <QuickActionCard
            title="Complete Your Profile"
            description="Add your skills, experience, and preferences to improve your matches."
            href="/profile"
            icon={User}
            variant="primary"
          />
          <QuickActionCard
            title="Browse Jobs"
            description="Explore job listings matched to your profile and preferences."
            href="/jobs"
            icon={Search}
          />
          <QuickActionCard
            title="Check ATS Score"
            description="Analyze your resume against job descriptions for compatibility."
            href="/dashboard"
            icon={FileCheck}
          />
        </div>
      </div>
    </div>
  );
}
