import type { Metadata } from "next";
import Link from "next/link";
import { Briefcase } from "lucide-react";
import { RegisterForm } from "@/components/auth/register-form";
import { OAuthButtons } from "@/components/auth/oauth-buttons";

export const metadata: Metadata = {
  title: "Create Account - Job Hunter",
  description: "Create a new Job Hunter account",
};

export default function RegisterPage() {
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
            Create your account to get started
          </p>
        </div>

        {/* Card */}
        <div className="rounded-xl border border-foreground/10 bg-background p-6 shadow-sm">
          <RegisterForm />
          <OAuthButtons />
        </div>

        {/* Footer link */}
        <p className="text-center text-sm text-foreground/60">
          Already have an account?{" "}
          <Link
            href="/login"
            className="font-medium text-blue-600 hover:underline"
          >
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
