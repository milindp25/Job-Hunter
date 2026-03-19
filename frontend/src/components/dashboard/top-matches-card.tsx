'use client';

import { Sparkles, TrendingUp, ArrowRight } from 'lucide-react';
import Link from 'next/link';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { MatchScoreBadge } from '@/components/jobs/match-score-badge';
import { useTopMatches, useMatchActions } from '@/hooks/useMatching';

function getRecommendationStyle(score: number): { label: string; className: string } {
  if (score >= 80) {
    return {
      label: 'Strong Match',
      className: 'bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-400',
    };
  }
  if (score >= 60) {
    return {
      label: 'Good Fit',
      className: 'bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-400',
    };
  }
  return {
    label: 'Worth a Look',
    className: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-950 dark:text-yellow-400',
  };
}

function MatchesSkeleton() {
  return (
    <div className="space-y-3" role="status">
      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i} className="h-14 animate-pulse rounded-lg bg-foreground/5" />
      ))}
      <span className="sr-only">Loading matches...</span>
    </div>
  );
}

export function TopMatchesCard() {
  const { matches, isLoading } = useTopMatches(5);
  const { runBulkAnalysis } = useMatchActions();

  const handleRunMatching = () => {
    runBulkAnalysis.mutate(undefined, {
      onSuccess: (data) => {
        toast.success(
          `Analyzed ${data.total_jobs_analyzed} jobs. ${data.new_matches} new matches found!`,
        );
      },
      onError: () => {
        toast.error('Failed to run matching analysis. Please try again.');
      },
    });
  };

  return (
    <div className="rounded-xl border border-foreground/10 bg-background p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-blue-600" />
          <h3 className="text-sm font-medium text-foreground/70">Your Top Matches</h3>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={handleRunMatching}
          loading={runBulkAnalysis.isPending}
        >
          <TrendingUp className="h-3.5 w-3.5" />
          Run Matching
        </Button>
      </div>

      <div className="mt-4">
        {isLoading ? (
          <MatchesSkeleton />
        ) : matches.length === 0 ? (
          <div className="flex flex-col items-center gap-3 py-6 text-center">
            <Sparkles className="h-8 w-8 text-foreground/20" />
            <div>
              <p className="text-sm font-medium text-foreground/70">No matches yet</p>
              <p className="mt-1 text-xs text-foreground/50">
                Run AI matching to find jobs that fit your profile.
              </p>
            </div>
            <Button size="sm" onClick={handleRunMatching} loading={runBulkAnalysis.isPending}>
              Run AI Matching
            </Button>
          </div>
        ) : (
          <ul className="space-y-2">
            {matches.map(({ match, job }) => {
              const rec = getRecommendationStyle(match.overall_score);
              return (
                <li
                  key={match.id}
                  className="flex items-center justify-between gap-3 rounded-lg border border-foreground/5 px-3 py-2.5 transition-colors hover:bg-foreground/[0.02]"
                >
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-foreground">{job.title}</p>
                    <p className="truncate text-xs text-foreground/60">{job.company}</p>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    <span
                      className={`hidden rounded-full px-2 py-0.5 text-xs font-medium sm:inline-flex ${rec.className}`}
                    >
                      {rec.label}
                    </span>
                    <MatchScoreBadge score={match.overall_score} />
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>

      {matches.length > 0 && (
        <div className="mt-4 border-t border-foreground/5 pt-3">
          <Link
            href="/jobs?tab=matches"
            className="inline-flex items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-700 hover:underline"
          >
            View All Matches
            <ArrowRight className="h-3 w-3" />
          </Link>
        </div>
      )}
    </div>
  );
}
