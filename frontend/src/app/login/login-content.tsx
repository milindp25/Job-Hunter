"use client";

import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { Briefcase, AlertCircle } from "lucide-react";
import { LoginForm } from "@/components/auth/login-form";
import { OAuthButtons } from "@/components/auth/oauth-buttons";

export function LoginContent() {
  const searchParams = useSearchParams();
  const error = searchParams.get("error");

  return (
    <div className="flex min-h-screen items-center justify-center px-4 py-12">
      <div className="w-full max-w-md space-y-8">
        {/* Logo */}
        <div className="flex flex-col items-center gap-2">
          <Link href="/" className="flex items-center gap-2">
            <Briefcase className="h-8 w-8 text-blue-600" strokeWidth={1.5} />
            <span className="text-2xl font-bold text-foreground">
              Job Hunter
            </span>
          </Link>
          <p className="text-sm text-foreground/60">
            Sign in to your account
          </p>
        </div>

        {/* OAuth Error Alert */}
        {error === "oauth_failed" && (
          <div className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 dark:border-red-900/50 dark:bg-red-950/20">
            <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-600 dark:text-red-400" strokeWidth={1.5} />
            <p className="text-sm text-red-700 dark:text-red-300">
              OAuth login failed. Please try again or use email/password.
            </p>
          </div>
        )}

        {/* Card */}
        <div className="rounded-xl border border-foreground/10 bg-background p-6 shadow-sm">
          <LoginForm />
          <OAuthButtons />
        </div>

        {/* Footer link */}
        <p className="text-center text-sm text-foreground/60">
          Don&apos;t have an account?{" "}
          <Link
            href="/register"
            className="font-medium text-blue-600 hover:underline"
          >
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}
