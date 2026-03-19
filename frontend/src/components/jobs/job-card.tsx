'use client';

import {
  MapPin,
  Bookmark,
  BookmarkCheck,
  ExternalLink,
  Clock,
  DollarSign,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { Job } from '@/lib/types';

interface JobCardProps {
  job: Job;
  isSaved: boolean;
  onSave: (jobId: string) => void;
  onUnsave: (jobId: string) => void;
  onSelect: (job: Job) => void;
  savingId: string | null;
}

function formatSalary(min: number | null, max: number | null, currency: string | null): string | null {
  if (!min && !max) return null;
  const cur = currency ?? 'USD';
  const fmt = (n: number) => `${cur === 'USD' ? '$' : cur + ' '}${Math.round(n / 1000)}k`;
  if (min && max) return `${fmt(min)} - ${fmt(max)}`;
  if (min) return `From ${fmt(min)}`;
  return `Up to ${fmt(max!)}`;
}

function timeAgo(dateStr: string | null): string {
  if (!dateStr) return 'Recently';
  const diff = Date.now() - new Date(dateStr).getTime();
  const days = Math.floor(diff / 86400000);
  if (days < 1) return 'Today';
  if (days === 1) return '1 day ago';
  if (days < 30) return `${days} days ago`;
  const months = Math.floor(days / 30);
  return months === 1 ? '1 month ago' : `${months} months ago`;
}

export function JobCard({ job, isSaved, onSave, onUnsave, onSelect, savingId }: JobCardProps) {
  const salary = formatSalary(job.salary_min, job.salary_max, job.salary_currency);
  const isSaving = savingId === job.id;

  return (
    <article
      className="group flex cursor-pointer flex-col rounded-xl border border-foreground/10 bg-background p-5 transition-all hover:border-foreground/20 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
      onClick={() => onSelect(job)}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect(job); } }}
      role="button"
      tabIndex={0}
      aria-label={`${job.title} at ${job.company}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <h3 className="truncate text-base font-semibold text-foreground">
            {job.title}
          </h3>
          <p className="mt-0.5 truncate text-sm text-foreground/70">{job.company}</p>
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="shrink-0"
          onClick={(e) => { e.stopPropagation(); if (isSaved) { onUnsave(job.id); } else { onSave(job.id); } }}
          disabled={isSaving}
          aria-label={isSaved ? 'Unsave job' : 'Save job'}
        >
          {isSaved ? (
            <BookmarkCheck className="h-4 w-4 text-blue-600" />
          ) : (
            <Bookmark className="h-4 w-4" />
          )}
        </Button>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-foreground/60">
        {job.is_remote ? (
          <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2 py-0.5 text-green-700 dark:bg-green-950 dark:text-green-400">
            <MapPin className="h-3 w-3" />
            Remote
          </span>
        ) : job.location ? (
          <span className="inline-flex items-center gap-1">
            <MapPin className="h-3 w-3" />
            {job.location}
          </span>
        ) : null}

        {salary && (
          <span className="inline-flex items-center gap-1">
            <DollarSign className="h-3 w-3" />
            {salary}
          </span>
        )}

        <span className="inline-flex items-center gap-1">
          <Clock className="h-3 w-3" />
          {timeAgo(job.posted_at)}
        </span>
      </div>

      {job.tags.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {job.tags.slice(0, 4).map((tag) => (
            <span
              key={tag}
              className="rounded-md bg-foreground/5 px-2 py-0.5 text-xs text-foreground/70"
            >
              {tag}
            </span>
          ))}
          {job.tags.length > 4 && (
            <span className="rounded-md bg-foreground/5 px-2 py-0.5 text-xs text-foreground/50">
              +{job.tags.length - 4}
            </span>
          )}
        </div>
      )}

      <div className="mt-auto flex items-center justify-between pt-4">
        <span className="rounded-md bg-foreground/5 px-2 py-0.5 text-xs text-foreground/50">
          {job.source}
        </span>
        <a
          href={job.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-700 hover:underline"
          onClick={(e) => e.stopPropagation()}
          aria-label={`Apply for ${job.title} (opens in new tab)`}
        >
          Apply
          <ExternalLink className="h-3 w-3" />
        </a>
      </div>
    </article>
  );
}
