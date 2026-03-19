'use client';

import { useCallback, useState } from 'react';
import Link from 'next/link';
import {
  Bookmark,
  BookmarkX,
  Briefcase,
  Building2,
  Calendar,
  DollarSign,
  ExternalLink,
  MapPin,
  StickyNote,
} from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { useSavedJobs, useJobActions } from '@/hooks/useJobs';
import type { SavedJob } from '@/lib/types';

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function formatSalary(min: number | null, max: number | null, currency: string | null): string | null {
  if (min === null && max === null) return null;
  const cur = currency ?? 'USD';
  const fmt = (n: number) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: cur, maximumFractionDigits: 0 }).format(n);
  if (min !== null && max !== null) return `${fmt(min)} - ${fmt(max)}`;
  if (min !== null) return `From ${fmt(min)}`;
  return `Up to ${fmt(max!)}`;
}

function SavedJobCardSkeleton() {
  return (
    <div className="animate-pulse rounded-xl border border-foreground/10 bg-background p-6">
      <div className="h-5 w-3/4 rounded bg-foreground/10" />
      <div className="mt-3 h-4 w-1/2 rounded bg-foreground/10" />
      <div className="mt-2 h-4 w-1/3 rounded bg-foreground/10" />
      <div className="mt-4 flex gap-2">
        <div className="h-9 w-24 rounded-lg bg-foreground/10" />
        <div className="h-9 w-20 rounded-lg bg-foreground/10" />
      </div>
    </div>
  );
}

function SavedJobCard({
  savedJob,
  onUnsave,
  isUnsaving,
}: {
  savedJob: SavedJob;
  onUnsave: (jobId: string) => void;
  isUnsaving: boolean;
}) {
  const { job, saved_at, notes } = savedJob;
  const salary = formatSalary(job.salary_min, job.salary_max, job.salary_currency);

  return (
    <div className="group rounded-xl border border-foreground/10 bg-background p-6 transition-shadow hover:shadow-md">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <Link
            href={`/jobs/${job.id}`}
            className="text-lg font-semibold text-foreground transition-colors hover:text-blue-600"
          >
            {job.title}
          </Link>

          <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-foreground/60">
            <span className="flex items-center gap-1.5">
              <Building2 className="h-3.5 w-3.5" />
              {job.company}
            </span>
            {job.location && (
              <span className="flex items-center gap-1.5">
                <MapPin className="h-3.5 w-3.5" />
                {job.location}
                {job.is_remote && ' (Remote)'}
              </span>
            )}
            {!job.location && job.is_remote && (
              <span className="flex items-center gap-1.5">
                <MapPin className="h-3.5 w-3.5" />
                Remote
              </span>
            )}
          </div>

          {salary && (
            <div className="mt-1.5 flex items-center gap-1.5 text-sm font-medium text-green-600 dark:text-green-400">
              <DollarSign className="h-3.5 w-3.5" />
              {salary}
            </div>
          )}

          <div className="mt-2 flex items-center gap-1.5 text-xs text-foreground/40">
            <Calendar className="h-3 w-3" />
            Saved {formatDate(saved_at)}
          </div>

          {notes && (
            <div className="mt-3 flex items-start gap-1.5 rounded-lg bg-foreground/5 px-3 py-2 text-sm text-foreground/70">
              <StickyNote className="mt-0.5 h-3.5 w-3.5 shrink-0" />
              <span>{notes}</span>
            </div>
          )}
        </div>

        <Bookmark className="h-5 w-5 shrink-0 fill-blue-600 text-blue-600" />
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <Button variant="outline" size="sm" asChild>
          <Link href={`/jobs/${job.id}`}>
            <Briefcase className="h-4 w-4" />
            View Job
          </Link>
        </Button>

        {job.url && (
          <Button variant="outline" size="sm" asChild>
            <a href={job.url} target="_blank" rel="noopener noreferrer">
              <ExternalLink className="h-4 w-4" />
              Apply
            </a>
          </Button>
        )}

        <Button
          variant="ghost"
          size="sm"
          className="text-red-600 hover:bg-red-50 hover:text-red-700 dark:hover:bg-red-950"
          onClick={() => onUnsave(job.id)}
          disabled={isUnsaving}
        >
          <BookmarkX className="h-4 w-4" />
          Unsave
        </Button>
      </div>
    </div>
  );
}

export function SavedJobsContent() {
  const { savedJobs, total, isLoading, error } = useSavedJobs();
  const { unsaveJob } = useJobActions();
  const [unsavingId, setUnsavingId] = useState<string | null>(null);

  const handleUnsave = useCallback(
    (jobId: string) => {
      setUnsavingId(jobId);
      unsaveJob.mutate(jobId, {
        onSuccess: () => {
          toast.success('Job removed from saved');
          setUnsavingId(null);
        },
        onError: () => {
          toast.error('Failed to remove saved job');
          setUnsavingId(null);
        },
      });
    },
    [unsaveJob],
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Saved Jobs</h1>
        <p className="mt-1 text-sm text-foreground/60">
          {total > 0
            ? `${total} saved job${total === 1 ? '' : 's'}`
            : 'Jobs you save will appear here'}
        </p>
      </div>

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
          Failed to load saved jobs. Please try again later.
        </div>
      )}

      {isLoading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <SavedJobCardSkeleton key={i} />
          ))}
        </div>
      )}

      {!isLoading && !error && savedJobs.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-foreground/10 bg-background px-6 py-16 text-center">
          <Bookmark className="h-12 w-12 text-foreground/20" />
          <h2 className="mt-4 text-lg font-semibold text-foreground">No saved jobs yet</h2>
          <p className="mt-1 text-sm text-foreground/60">
            Browse jobs to save some!
          </p>
          <Button className="mt-6" asChild>
            <Link href="/jobs">Browse Jobs</Link>
          </Button>
        </div>
      )}

      {!isLoading && !error && savedJobs.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {savedJobs.map((savedJob) => (
            <SavedJobCard
              key={savedJob.id}
              savedJob={savedJob}
              onUnsave={handleUnsave}
              isUnsaving={unsavingId === savedJob.job.id}
            />
          ))}
        </div>
      )}
    </div>
  );
}
