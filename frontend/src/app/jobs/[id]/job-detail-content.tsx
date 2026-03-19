'use client';

import { useCallback, useMemo, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  ArrowLeft,
  Bookmark,
  BookmarkCheck,
  Briefcase,
  Clock,
  DollarSign,
  ExternalLink,
  MapPin,
} from 'lucide-react';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/loading-skeleton';
import { AtsCheckButton } from '@/components/ats/ats-check-button';
import { TailorButton } from '@/components/tailor/tailor-button';
import { useSavedJobs, useJobActions } from '@/hooks/useJobs';
import { useResumes } from '@/hooks/useResumes';
import type { Job } from '@/lib/types';

interface JobDetailContentProps {
  jobId: string;
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

function JobDetailSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Skeleton className="h-10 w-10" />
        <Skeleton className="h-6 w-48" />
      </div>
      <div className="rounded-xl border border-foreground/10 bg-background p-6 space-y-5">
        <Skeleton className="h-8 w-2/3" />
        <Skeleton className="h-5 w-1/3" />
        <div className="flex gap-3">
          <Skeleton className="h-7 w-24 rounded-full" />
          <Skeleton className="h-7 w-32 rounded-full" />
          <Skeleton className="h-7 w-28 rounded-full" />
        </div>
        <div className="space-y-2 pt-4">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-5/6" />
          <Skeleton className="h-4 w-4/6" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
        </div>
        <div className="flex gap-3 pt-4">
          <Skeleton className="h-10 w-36" />
          <Skeleton className="h-10 w-24" />
        </div>
      </div>
    </div>
  );
}

export function JobDetailContent({ jobId }: JobDetailContentProps) {
  const router = useRouter();
  const [savingId, setSavingId] = useState<string | null>(null);

  const { data: job, isLoading, error } = useQuery({
    queryKey: ['job', jobId],
    queryFn: async (): Promise<Job> => {
      const { data } = await api.get<Job>(`/jobs/${jobId}`);
      return data;
    },
  });

  const { savedJobs } = useSavedJobs();
  const { saveJob, unsaveJob } = useJobActions();
  const { resumes } = useResumes();

  const primaryResume = resumes.find((r) => r.is_primary) ?? resumes[0] ?? null;

  const savedJobIds = useMemo(
    () => new Set(savedJobs.map((sj) => sj.job.id)),
    [savedJobs],
  );

  const isSaved = job ? savedJobIds.has(job.id) : false;
  const isSaving = job ? savingId === job.id : false;

  const handleSave = useCallback(
    (id: string) => {
      setSavingId(id);
      saveJob.mutate(id, {
        onSuccess: () => {
          toast.success('Job saved');
          setSavingId(null);
        },
        onError: () => {
          toast.error('Failed to save job');
          setSavingId(null);
        },
      });
    },
    [saveJob],
  );

  const handleUnsave = useCallback(
    (id: string) => {
      setSavingId(id);
      unsaveJob.mutate(id, {
        onSuccess: () => {
          toast.success('Job removed from saved');
          setSavingId(null);
        },
        onError: () => {
          toast.error('Failed to remove saved job');
          setSavingId(null);
        },
      });
    },
    [unsaveJob],
  );

  if (isLoading) {
    return <JobDetailSkeleton />;
  }

  if (error || !job) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-12 text-center">
        <h1 className="text-xl font-bold text-foreground">Job not found</h1>
        <p className="mt-2 text-foreground/60">
          The job listing you are looking for does not exist or is no longer available.
        </p>
        <Button asChild className="mt-6">
          <Link href="/jobs">Back to Jobs</Link>
        </Button>
      </div>
    );
  }

  const salary = formatSalary(job.salary_min, job.salary_max, job.salary_currency);

  return (
    <div className="space-y-6">
      {/* Back button */}
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" asChild>
          <Link href="/jobs" aria-label="Back to jobs">
            <ArrowLeft className="h-5 w-5" />
          </Link>
        </Button>
        <h2 className="text-sm font-medium text-foreground/60">Back to Jobs</h2>
      </div>

      {/* Job detail card */}
      <div className="rounded-xl border border-foreground/10 bg-background p-6 shadow-sm">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-foreground">{job.title}</h1>
          <p className="mt-1 text-lg text-foreground/70">{job.company}</p>
        </div>

        {/* Meta badges */}
        <div className="mt-4 flex flex-wrap items-center gap-3 text-sm text-foreground/60">
          {job.is_remote ? (
            <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2.5 py-1 text-green-700 dark:bg-green-950 dark:text-green-400">
              <MapPin className="h-3.5 w-3.5" />
              Remote
            </span>
          ) : job.location ? (
            <span className="inline-flex items-center gap-1">
              <MapPin className="h-3.5 w-3.5" />
              {job.location}
            </span>
          ) : null}

          {salary && (
            <span className="inline-flex items-center gap-1">
              <DollarSign className="h-3.5 w-3.5" />
              {salary}
            </span>
          )}

          {job.job_type && (
            <span className="inline-flex items-center gap-1">
              <Briefcase className="h-3.5 w-3.5" />
              {job.job_type.replace('_', ' ')}
            </span>
          )}

          <span className="inline-flex items-center gap-1">
            <Clock className="h-3.5 w-3.5" />
            {timeAgo(job.posted_at)}
          </span>
        </div>

        {/* Tags */}
        {job.tags.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-1.5">
            {job.tags.map((tag) => (
              <span
                key={tag}
                className="rounded-md bg-foreground/5 px-2.5 py-1 text-xs text-foreground/70"
              >
                {tag}
              </span>
            ))}
          </div>
        )}

        {/* Description */}
        <div className="mt-6">
          <h3 className="mb-2 text-sm font-semibold text-foreground">Description</h3>
          <div className="whitespace-pre-wrap text-sm leading-relaxed text-foreground/80">
            {job.description}
          </div>
        </div>

        {/* Source */}
        <div className="mt-4 text-xs text-foreground/40">
          Source: {job.source}
        </div>

        {/* Action buttons */}
        <div className="mt-6 flex flex-wrap items-center gap-3">
          <Button asChild>
            <a href={job.url} target="_blank" rel="noopener noreferrer">
              Apply Now
              <ExternalLink className="h-4 w-4" />
            </a>
          </Button>

          <Button
            variant="outline"
            onClick={() => isSaved ? handleUnsave(job.id) : handleSave(job.id)}
            disabled={isSaving}
            aria-label={isSaved ? 'Unsave job' : 'Save job'}
          >
            {isSaved ? (
              <>
                <BookmarkCheck className="h-4 w-4 text-blue-600" />
                Saved
              </>
            ) : (
              <>
                <Bookmark className="h-4 w-4" />
                Save
              </>
            )}
          </Button>
        </div>

        {/* ATS + Tailor section */}
        {primaryResume && (
          <>
            <div className="my-6 h-px bg-foreground/10" />
            <div className="flex flex-wrap items-start gap-6">
              <div>
                <h4 className="mb-2 text-sm font-semibold text-foreground">ATS Compliance Check</h4>
                <AtsCheckButton
                  resumeId={primaryResume.id}
                  jobId={job.id}
                  onSuccess={(result) => router.push(`/ats?checkId=${result.id}`)}
                />
              </div>
              <div>
                <h4 className="mb-2 text-sm font-semibold text-foreground">Tailor Resume</h4>
                <TailorButton
                  resumeId={primaryResume.id}
                  jobId={job.id}
                />
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
