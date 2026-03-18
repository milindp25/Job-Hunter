"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuthStore } from "@/hooks/useAuth";
import { useProfile } from "@/hooks/useProfile";

function AuthGuardSkeleton() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center" role="status">
      <div className="w-full max-w-md space-y-6 px-4">
        <div className="mx-auto h-8 w-48 animate-pulse rounded-lg bg-foreground/10" />
        <div className="space-y-3">
          <div className="h-4 w-full animate-pulse rounded bg-foreground/10" />
          <div className="h-4 w-3/4 animate-pulse rounded bg-foreground/10" />
          <div className="h-4 w-1/2 animate-pulse rounded bg-foreground/10" />
        </div>
        <div className="h-10 w-full animate-pulse rounded-lg bg-foreground/10" />
      </div>
      <span className="sr-only">Loading...</span>
    </div>
  );
}

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, isLoading: authLoading, fetchUser } = useAuthStore();
  const { profile, isLoading: profileLoading } = useProfile();

  useEffect(() => {
    if (!isAuthenticated && !authLoading) {
      fetchUser();
    }
  }, [isAuthenticated, authLoading, fetchUser]);

  useEffect(() => {
    if (authLoading || profileLoading) return;

    if (!isAuthenticated) {
      router.replace("/login");
      return;
    }

    if (
      profile &&
      !profile.onboarding_completed &&
      pathname !== "/onboarding"
    ) {
      router.replace("/onboarding");
    }
  }, [isAuthenticated, authLoading, profileLoading, profile, pathname, router]);

  if (authLoading || profileLoading) {
    return <AuthGuardSkeleton />;
  }

  if (!isAuthenticated) {
    return <AuthGuardSkeleton />;
  }

  return <>{children}</>;
}
