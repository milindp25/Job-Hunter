'use client';

import * as Dialog from '@radix-ui/react-dialog';
import {
  X,
  MapPin,
  DollarSign,
  Briefcase,
  Clock,
  ExternalLink,
  Bookmark,
  BookmarkCheck,
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { AtsCheckButton } from '@/components/ats/ats-check-button';
import { useResumes } from '@/hooks/useResumes';
import type { Job } from '@/lib/types';

interface JobDetailModalProps {
  job: Job | null;
  open: boolean;
  onClose: () => void;
  isSaved: boolean;
  onSave: (jobId: string) => void;
  onUnsave: (jobId: string) => void;
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

export function JobDetailModal({
  job,
  open,
  onClose,
  isSaved,
  onSave,
  onUnsave,
  savingId,
}: JobDetailModalProps) {
  const router = useRouter();
  const { resumes } = useResumes();
  const primaryResume = resumes.find((r) => r.is_primary) ?? resumes[0] ?? null;

  if (!job) return null;

  const salary = formatSalary(job.salary_min, job.salary_max, job.salary_currency);
  const isSaving = savingId === job.id;

  return (
    <Dialog.Root open={open} onOpenChange={(isOpen) => { if (!isOpen) onClose(); }}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/50 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
        <Dialog.Content
          className="fixed left-1/2 top-1/2 z-50 w-full max-w-2xl -translate-x-1/2 -translate-y-1/2 rounded-xl border border-foreground/10 bg-background p-6 shadow-xl focus:outline-none data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 max-h-[85vh] overflow-y-auto"
          aria-describedby="job-detail-description"
        >
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0 flex-1">
              <Dialog.Title className="text-xl font-bold text-foreground">
                {job.title}
              </Dialog.Title>
              <p className="mt-1 text-base text-foreground/70">{job.company}</p>
            </div>
            <Dialog.Close asChild>
              <Button variant="ghost" size="icon" aria-label="Close dialog">
                <X className="h-4 w-4" />
              </Button>
            </Dialog.Close>
          </div>

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

          <div id="job-detail-description" className="mt-6">
            <h4 className="mb-2 text-sm font-semibold text-foreground">Description</h4>
            <div className="whitespace-pre-wrap text-sm leading-relaxed text-foreground/80">
              {job.description}
            </div>
          </div>

          <div className="mt-4 text-xs text-foreground/40">
            Source: {job.source}
          </div>

          <div className="mt-6 flex items-center gap-3">
            <Button asChild className="flex-1">
              <a href={job.url} target="_blank" rel="noopener noreferrer">
                Apply Now
                <ExternalLink className="h-4 w-4" />
              </a>
            </Button>
            <Button
              variant="outline"
              onClick={() => isSaved ? onUnsave(job.id) : onSave(job.id)}
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

          {primaryResume && (
            <>
              <div className="my-4 h-px bg-foreground/10" />
              <div>
                <h4 className="mb-2 text-sm font-semibold text-foreground">ATS Compliance Check</h4>
                <AtsCheckButton
                  resumeId={primaryResume.id}
                  jobId={job.id}
                  onSuccess={(result) => router.push(`/ats?checkId=${result.id}`)}
                />
              </div>
            </>
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
