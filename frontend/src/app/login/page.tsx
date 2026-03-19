import type { Metadata } from "next";
import { Suspense } from "react";
import { LoginContent } from "./login-content";

export const metadata: Metadata = {
  title: "Sign In - Job Hunter",
  description: "Sign in to your Job Hunter account",
};

export default function LoginPage() {
  return (
    <Suspense>
      <LoginContent />
    </Suspense>
  );
}
