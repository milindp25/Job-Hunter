"use client";

import { use } from "react";
import Link from "next/link";
import { ArrowLeft, Loader2, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { TailorDiffView } from "@/components/tailor/tailor-diff-view";
import { KeywordAnalysis } from "@/components/tailor/keyword-analysis";
import { useTailoredResume } from "@/hooks/useTailoredResume";

interface TailorResultPageProps {
  params: Promise<{ id: string }>;
}

export default function TailorResultPage({ params }: TailorResultPageProps) {
  const { id } = use(params);
  const { data: tailored, isLoading, error } = useTailoredResume(
    id === "0" ? null : id,
  );

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (error || !tailored) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-12 text-center">
        <h1 className="text-xl font-bold text-foreground">
          Tailored resume not found
        </h1>
        <p className="mt-2 text-foreground/60">
          The tailored resume you are looking for does not exist or you do not
          have access.
        </p>
        <Button asChild className="mt-6">
          <Link href="/dashboard">Back to Dashboard</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" asChild>
            <Link href="/dashboard" aria-label="Back to dashboard">
              <ArrowLeft className="h-5 w-5" />
            </Link>
          </Button>
          <div>
            <h1 className="flex items-center gap-2 text-2xl font-bold text-foreground">
              <Sparkles className="h-6 w-6 text-blue-600" />
              Tailored Resume
            </h1>
            <p className="mt-1 text-sm text-foreground/60">
              AI-optimized for job #{tailored.job_id}
            </p>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="grid gap-8 lg:grid-cols-[1fr_300px]">
        <div>
          <TailorDiffView tailored={tailored} />
        </div>

        {/* Sidebar */}
        <aside className="space-y-6">
          <div className="sticky top-24 rounded-xl border border-foreground/10 bg-background p-6 shadow-sm">
            <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold text-foreground">
              <Sparkles className="h-4 w-4 text-blue-600" />
              Keyword Analysis
            </h2>
            <KeywordAnalysis tailored={tailored} />
          </div>
        </aside>
      </div>
    </div>
  );
}
