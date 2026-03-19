'use client';

import { useCallback } from 'react';
import { FileText } from 'lucide-react';
import { toast } from 'sonner';
import { useResumes } from '@/hooks/useResumes';
import { ResumeUploadZone } from './resume-upload-zone';
import { ResumeCard } from './resume-card';

function ResumeListSkeleton() {
  return (
    <div className="space-y-3" role="status">
      {[1, 2].map((i) => (
        <div
          key={i}
          className="flex items-center gap-4 rounded-lg border border-foreground/10 p-4"
        >
          <div className="h-10 w-10 animate-pulse rounded-lg bg-foreground/10" />
          <div className="flex-1 space-y-2">
            <div className="h-4 w-48 animate-pulse rounded bg-foreground/10" />
            <div className="h-3 w-32 animate-pulse rounded bg-foreground/10" />
          </div>
        </div>
      ))}
      <span className="sr-only">Loading resumes...</span>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center gap-3 py-12 text-center">
      <FileText className="h-12 w-12 text-foreground/20" aria-hidden="true" />
      <div>
        <p className="text-sm font-medium text-foreground/70">No resumes uploaded yet.</p>
        <p className="text-xs text-foreground/50 mt-1">
          Upload your first resume to get started.
        </p>
      </div>
    </div>
  );
}

export function ResumeManager() {
  const {
    resumes,
    total,
    isLoading,
    uploadResume,
    deleteResume,
    setPrimary,
    getDownloadUrl,
  } = useResumes();

  const handleFileSelected = useCallback(
    (file: File) => {
      uploadResume.mutate(file, {
        onSuccess: () => {
          toast.success(`"${file.name}" uploaded successfully.`);
        },
        onError: () => {
          toast.error('Failed to upload resume. Please try again.');
        },
      });
    },
    [uploadResume],
  );

  const handleDownload = useCallback(
    async (resumeId: string) => {
      try {
        const url = await getDownloadUrl(resumeId);
        window.open(url, '_blank', 'noopener,noreferrer');
      } catch {
        toast.error('Failed to get download link. Please try again.');
      }
    },
    [getDownloadUrl],
  );

  const handleSetPrimary = useCallback(
    (resumeId: string) => {
      setPrimary.mutate(resumeId, {
        onSuccess: () => {
          toast.success('Primary resume updated.');
        },
        onError: () => {
          toast.error('Failed to update primary resume.');
        },
      });
    },
    [setPrimary],
  );

  const handleDelete = useCallback(
    (resumeId: string) => {
      deleteResume.mutate(resumeId, {
        onSuccess: () => {
          toast.success('Resume deleted.');
        },
        onError: () => {
          toast.error('Failed to delete resume.');
        },
      });
    },
    [deleteResume],
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <h2 className="text-lg font-semibold text-foreground">Resumes</h2>
        {total > 0 && (
          <span className="rounded-full bg-foreground/10 px-2.5 py-0.5 text-xs font-medium text-foreground/70">
            {total}
          </span>
        )}
      </div>

      <ResumeUploadZone
        onFileSelected={handleFileSelected}
        isUploading={uploadResume.isPending}
      />

      {isLoading ? (
        <ResumeListSkeleton />
      ) : resumes.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="space-y-3" role="list" aria-label="Uploaded resumes">
          {resumes.map((resume) => (
            <div key={resume.id} role="listitem">
              <ResumeCard
                resume={resume}
                onDownload={handleDownload}
                onSetPrimary={handleSetPrimary}
                onDelete={handleDelete}
                isSettingPrimary={
                  setPrimary.isPending && setPrimary.variables === resume.id
                }
                isDeleting={
                  deleteResume.isPending && deleteResume.variables === resume.id
                }
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
