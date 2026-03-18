import type { Metadata } from "next";
import Link from "next/link";
import { Briefcase } from "lucide-react";
import { LoginForm } from "@/components/auth/login-form";
import { OAuthButtons } from "@/components/auth/oauth-buttons";

export const metadata: Metadata = {
  title: "Sign In - Job Hunter",
  description: "Sign in to your Job Hunter account",
};

export default function LoginPage() {
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
