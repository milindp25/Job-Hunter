'use client';

import { useCallback } from 'react';
import { useSearchParams } from 'next/navigation';
import {
  FileText,
  Hash,
  AlignLeft,
  Lightbulb,
  ClipboardList,
} from 'lucide-react';
import { AuthGuard } from '@/components/layout/auth-guard';
import { AtsScoreHeader } from '@/components/ats/ats-score-header';
import { AtsFindingsSection } from '@/components/ats/ats-findings-section';
import { AtsSuggestionCard } from '@/components/ats/ats-suggestion-card';
import { AtsStaleBanner } from '@/components/ats/ats-stale-banner';
import { AtsCheckButton } from '@/components/ats/ats-check-button';
import { useAtsCheck, useDismissFinding } from '@/hooks/useAtsCheck';
import type { AtsCheck, AtsFinding } from '@/lib/types';

// ---------------------------------------------------------------------------
// Loading skeleton
// ---------------------------------------------------------------------------

function ReportSkeleton() {
  return (
    <div className="space-y-6" role="status" aria-label="Loading ATS report">
      {/* Score header skeleton */}
      <div className="flex gap-4">
        <div className="h-44 w-44 animate-pulse rounded-2xl bg-foreground/10" />
        <div className="grid flex-1 grid-cols-3 gap-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-36 animate-pulse rounded-xl bg-foreground/10" />
          ))}
        </div>
      </div>
      {/* Findings skeleton */}
      {[1, 2, 3].map((i) => (
        <div key={i} className="space-y-2">
          <div className="h-6 w-40 animate-pulse rounded bg-foreground/10" />
          <div className="h-16 w-full animate-pulse rounded-lg bg-foreground/10" />
          <div className="h-16 w-full animate-pulse rounded-lg bg-foreground/10" />
        </div>
      ))}
      <span className="sr-only">Loading…</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Empty state
// ---------------------------------------------------------------------------

function CheckNotFound() {
  return (
    <div className="flex flex-col items-center gap-4 py-20 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-foreground/8">
        <ClipboardList className="h-8 w-8 text-foreground/30" aria-hidden="true" />
      </div>
      <div>
        <h2 className="text-lg font-semibold text-foreground">Check not found</h2>
        <p className="mt-1 text-sm text-foreground/50">
          The ATS check you&apos;re looking for doesn&apos;t exist or you don&apos;t have access to it.
        </p>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Report body (rendered once we have data)
// ---------------------------------------------------------------------------

interface ReportBodyProps {
  check: AtsCheck;
  onRerun: () => void;
}

function ReportBody({ check, onRerun }: ReportBodyProps) {
  const { mutate: dismissFinding } = useDismissFinding();

  const handleDismiss = useCallback(
    (findingId: string, dismissed: boolean) => {
      dismissFinding({ checkId: check.id, findingId, dismissed });
    },
    [check.id, dismissFinding],
  );

  const findingsByCategory = useCallback(
    (category: AtsFinding['category']) =>
      check.findings.filter((f) => f.category === category),
    [check.findings],
  );

  const formatFindings = findingsByCategory('format');
  const keywordFindings = findingsByCategory('keyword');
  const contentFindings = findingsByCategory('content');

  return (
    <div className="space-y-8">
      {/* Stale banner */}
      <AtsStaleBanner isStale={check.is_stale} onRerun={onRerun} />

      {/* Score header */}
      <AtsScoreHeader
        overallScore={check.overall_score}
        formatScore={check.format_score}
        keywordScore={check.keyword_score}
        contentScore={check.content_score}
      />

      {/* Meta info */}
      <div className="flex flex-wrap gap-3 text-xs text-foreground/40">
        <span>
          Check type:{' '}
          <span className="font-medium text-foreground/60">
            {check.check_type === 'full' ? 'Full (format + AI)' : 'Format only'}
          </span>
        </span>
        <span aria-hidden="true">·</span>
        <span>
          Run:{' '}
          <span className="font-medium text-foreground/60">
            {new Date(check.created_at).toLocaleDateString(undefined, {
              dateStyle: 'medium',
            })}
          </span>
        </span>
        {check.ai_analysis_available && (
          <>
            <span aria-hidden="true">·</span>
            <span className="rounded-full bg-blue-100 px-2 py-0.5 font-medium text-blue-700 dark:bg-blue-950/40 dark:text-blue-300">
              AI analysis included
            </span>
          </>
        )}
      </div>

      {/* Findings sections */}
      <div className="space-y-10">
        <AtsFindingsSection
          category="format"
          title="Format &amp; Parsing"
          icon={<FileText className="h-5 w-5" />}
          score={check.format_score}
          findings={formatFindings}
          onDismiss={handleDismiss}
        />

        <AtsFindingsSection
          category="keyword"
          title="Keyword Coverage"
          icon={<Hash className="h-5 w-5" />}
          score={check.keyword_score}
          findings={keywordFindings}
          onDismiss={handleDismiss}
        />

        <AtsFindingsSection
          category="content"
          title="Content Quality"
          icon={<AlignLeft className="h-5 w-5" />}
          score={check.content_score}
          findings={contentFindings}
          onDismiss={handleDismiss}
        />
      </div>

      {/* Suggestions */}
      {check.suggestions.length > 0 && (
        <section aria-label="AI suggestions">
          <div className="mb-4 flex items-center gap-2">
            <Lightbulb className="h-5 w-5 text-amber-500" aria-hidden="true" />
            <h2 className="text-base font-semibold text-foreground">
              AI Suggestions
            </h2>
            <span className="rounded-full bg-foreground/10 px-2 py-0.5 text-xs font-medium text-foreground/60">
              {check.suggestions.length}
            </span>
          </div>
          <div className="space-y-4">
            {check.suggestions.map((s, i) => (
              // suggestions have no stable id — use composite key
              <AtsSuggestionCard key={`${s.section}-${i}`} suggestion={s} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main export (AuthGuard + data fetching)
// ---------------------------------------------------------------------------

export function AtsReportContent() {
  const searchParams = useSearchParams();
  const checkId = searchParams.get('checkId');

  const { check, isLoading, error } = useAtsCheck(checkId);

  // For re-run we just let the user click AtsCheckButton with resume from check
  // We need a rerun handler that navigates or refreshes — simplest: page reload
  const handleRerun = useCallback(() => {
    if (!check) return;
    // Trigger a new check with the same resume/job via the check button
    // We surface a dedicated button instead of doing it silently
  }, [check]);

  return (
    <AuthGuard>
      <main className="mx-auto w-full max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Page header */}
        <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground">ATS Compliance Report</h1>
            <p className="mt-1 text-sm text-foreground/50">
              Detailed ATS compatibility analysis for your resume
            </p>
          </div>
          {check && (
            <AtsCheckButton
              resumeId={check.resume_id}
              jobId={check.job_id ?? undefined}
              onSuccess={(newCheck) => {
                // Navigate to new check result
                const url = new URL(window.location.href);
                url.searchParams.set('checkId', newCheck.id);
                window.history.pushState({}, '', url.toString());
                window.location.reload();
              }}
            />
          )}
        </div>

        {/* Content */}
        {isLoading && <ReportSkeleton />}
        {!isLoading && (error || !check) && !checkId && (
          <div className="rounded-xl border border-foreground/10 bg-foreground/3 px-4 py-8 text-center text-sm text-foreground/40">
            No check selected. Provide a <code className="rounded bg-foreground/10 px-1">checkId</code>{' '}
            query parameter to view a report.
          </div>
        )}
        {!isLoading && (error || !check) && checkId && <CheckNotFound />}
        {!isLoading && check && (
          <ReportBody check={check} onRerun={handleRerun} />
        )}
      </main>
    </AuthGuard>
  );
}
