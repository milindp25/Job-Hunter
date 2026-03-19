'use client';

import { useCallback, useMemo, useState } from 'react';
import { Filter, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { JobFilters } from '@/components/jobs/job-filters';
import { JobList } from '@/components/jobs/job-list';
import { JobDetailModal } from '@/components/jobs/job-detail-modal';
import { useJobs, useSavedJobs, useJobActions } from '@/hooks/useJobs';
import type { Job, JobSearchParams } from '@/lib/types';

export function JobsContent() {
  const [filters, setFilters] = useState<JobSearchParams>({ page: 1, page_size: 18 });
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false);
  const [savingId, setSavingId] = useState<string | null>(null);

  const { jobs, total, page, pageSize, isLoading } = useJobs(filters);
  const { savedJobs } = useSavedJobs();
  const { saveJob, unsaveJob, fetchJobs } = useJobActions();

  const savedJobIds = useMemo(
    () => new Set(savedJobs.map((sj) => sj.job.id)),
    [savedJobs],
  );

  const handleFilterChange = useCallback((newFilters: JobSearchParams) => {
    setFilters((prev) => ({ ...prev, ...newFilters }));
  }, []);

  const handlePageChange = useCallback((newPage: number) => {
    setFilters((prev) => ({ ...prev, page: newPage }));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  const handleSelectJob = useCallback((job: Job) => {
    setSelectedJob(job);
    setModalOpen(true);
  }, []);

  const handleSave = useCallback(
    (jobId: string) => {
      setSavingId(jobId);
      saveJob.mutate(jobId, {
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
    (jobId: string) => {
      setSavingId(jobId);
      unsaveJob.mutate(jobId, {
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

  function handleFetchJobs() {
    fetchJobs.mutate(undefined, {
      onSuccess: (data) => {
        toast.success(
          `Fetched ${data.total_new_jobs} new and ${data.total_updated_jobs} updated jobs`,
        );
      },
      onError: () => {
        toast.error('Failed to fetch new jobs');
      },
    });
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Browse Jobs</h1>
          <p className="mt-1 text-sm text-foreground/60">
            {total > 0
              ? `${total} job${total === 1 ? '' : 's'} found`
              : 'Search and filter job listings'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            className="lg:hidden"
            onClick={() => setMobileFiltersOpen(!mobileFiltersOpen)}
            aria-expanded={mobileFiltersOpen}
            aria-label="Toggle filters"
          >
            <Filter className="h-4 w-4" />
            Filters
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleFetchJobs}
            loading={fetchJobs.isPending}
          >
            <RefreshCw className="h-4 w-4" />
            Fetch New Jobs
          </Button>
        </div>
      </div>

      <div className="flex gap-6">
        {/* Desktop sidebar */}
        <aside className="hidden w-64 shrink-0 lg:block">
          <div className="sticky top-24 rounded-xl border border-foreground/10 bg-background p-4">
            <h2 className="mb-4 text-sm font-semibold text-foreground">Filters</h2>
            <JobFilters filters={filters} onFilterChange={handleFilterChange} />
          </div>
        </aside>

        {/* Mobile filters drawer */}
        {mobileFiltersOpen && (
          <div className="fixed inset-0 z-40 lg:hidden">
            <div
              className="absolute inset-0 bg-black/30"
              onClick={() => setMobileFiltersOpen(false)}
              onKeyDown={(e) => { if (e.key === 'Escape') setMobileFiltersOpen(false); }}
              role="button"
              tabIndex={0}
              aria-label="Close filters"
            />
            <div className="absolute bottom-0 left-0 right-0 max-h-[70vh] overflow-y-auto rounded-t-2xl border-t border-foreground/10 bg-background p-6">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-sm font-semibold text-foreground">Filters</h2>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setMobileFiltersOpen(false)}
                >
                  Done
                </Button>
              </div>
              <JobFilters filters={filters} onFilterChange={handleFilterChange} />
            </div>
          </div>
        )}

        {/* Job grid */}
        <div className="min-w-0 flex-1">
          <JobList
            jobs={jobs}
            savedJobIds={savedJobIds}
            isLoading={isLoading}
            page={page}
            pageSize={pageSize}
            total={total}
            onPageChange={handlePageChange}
            onSave={handleSave}
            onUnsave={handleUnsave}
            onSelect={handleSelectJob}
            savingId={savingId}
          />
        </div>
      </div>

      <JobDetailModal
        job={selectedJob}
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        isSaved={selectedJob ? savedJobIds.has(selectedJob.id) : false}
        onSave={handleSave}
        onUnsave={handleUnsave}
        savingId={savingId}
      />
    </div>
  );
}
