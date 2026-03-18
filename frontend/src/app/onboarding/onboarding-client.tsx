"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Briefcase, Loader2 } from "lucide-react";
import { useAuthStore } from "@/hooks/useAuth";
import { OnboardingWizard } from "@/components/onboarding/onboarding-wizard";

export function OnboardingClient() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, fetchUser } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated && !isLoading) {
      fetchUser();
    }
  }, [isAuthenticated, isLoading, fetchUser]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading || !isAuthenticated) {
    return (
      <div
        className="flex min-h-[60vh] items-center justify-center"
        role="status"
      >
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          <p className="text-sm text-foreground/50">Loading...</p>
        </div>
        <span className="sr-only">Loading your profile...</span>
      </div>
    );
  }

  return (
    <main className="flex min-h-screen flex-col">
      {/* Minimal header for onboarding */}
      <header className="border-b border-foreground/10 px-4 py-4">
        <div className="mx-auto flex max-w-3xl items-center gap-2">
          <Briefcase className="h-6 w-6 text-blue-600" strokeWidth={1.5} />
          <span className="text-lg font-bold text-foreground">Job Hunter</span>
          <span className="ml-2 rounded-md bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700 dark:bg-blue-900/40 dark:text-blue-300">
            Setup
          </span>
        </div>
      </header>

      {/* Wizard content */}
      <div className="flex-1 px-4 py-8 sm:py-12">
        <OnboardingWizard userName={user?.full_name} />
      </div>
    </main>
  );
}
