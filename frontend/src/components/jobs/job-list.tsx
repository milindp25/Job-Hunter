'use client';

import { ChevronLeft, ChevronRight, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { JobCard } from './job-card';
import type { Job } from '@/lib/types';

interface JobListProps {
  jobs: Job[];
  savedJobIds: Set<string>;
  isLoading: boolean;
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
  onSave: (jobId: string) => void;
  onUnsave: (jobId: string) => void;
  onSelect: (job: Job) => void;
  savingId: string | null;
}

function JobCardSkeleton() {
  return (
    <div className="animate-pulse rounded-xl border border-foreground/10 bg-background p-5">
      <div className="flex items-start justify-between">
        <div className="flex-1 space-y-2">
          <div className="h-5 w-3/4 rounded bg-foreground/10" />
          <div className="h-4 w-1/2 rounded bg-foreground/10" />
        </div>
        <div className="h-8 w-8 rounded bg-foreground/10" />
      </div>
      <div className="mt-3 flex gap-2">
        <div className="h-5 w-20 rounded-full bg-foreground/10" />
        <div className="h-5 w-16 rounded-full bg-foreground/10" />
      </div>
      <div className="mt-3 flex gap-1.5">
        <div className="h-5 w-14 rounded bg-foreground/10" />
        <div className="h-5 w-14 rounded bg-foreground/10" />
        <div className="h-5 w-14 rounded bg-foreground/10" />
      </div>
    </div>
  );
}

export function JobList({
  jobs,
  savedJobIds,
  isLoading,
  page,
  pageSize,
  total,
  onPageChange,
  onSave,
  onUnsave,
  onSelect,
  savingId,
}: JobListProps) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  if (isLoading) {
    return (
      <div className="space-y-4" role="status">
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <JobCardSkeleton key={i} />
          ))}
        </div>
        <span className="sr-only">Loading jobs...</span>
      </div>
    );
  }

  if (jobs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-foreground/20 py-16">
        <Search className="h-10 w-10 text-foreground/30" />
        <h3 className="mt-4 text-base font-semibold text-foreground">No jobs found</h3>
        <p className="mt-1 text-sm text-foreground/60">
          Try adjusting your filters or fetch new jobs.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {jobs.map((job) => (
          <JobCard
            key={job.id}
            job={job}
            isSaved={savedJobIds.has(job.id)}
            onSave={onSave}
            onUnsave={onUnsave}
            onSelect={onSelect}
            savingId={savingId}
          />
        ))}
      </div>

      {totalPages > 1 && (
        <nav
          className="flex items-center justify-center gap-2 pt-4"
          aria-label="Job list pagination"
        >
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            aria-label="Previous page"
          >
            <ChevronLeft className="h-4 w-4" />
            Previous
          </Button>
          <span className="px-3 text-sm text-foreground/60">
            Page {page} of {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
            aria-label="Next page"
          >
            Next
            <ChevronRight className="h-4 w-4" />
          </Button>
        </nav>
      )}
    </div>
  );
}
