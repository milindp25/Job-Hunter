'use client';

import { useState } from 'react';
import Link from 'next/link';
import { FileText, Download, Trash2, Star, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { AtsFormatBadge } from '@/components/ats/ats-format-badge';
import { useAtsResults } from '@/hooks/useAtsCheck';
import { cn } from '@/lib/utils';
import type { Resume } from '@/lib/types';

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

interface ResumeCardProps {
  resume: Resume;
  onDownload: (resumeId: string) => Promise<void>;
  onSetPrimary: (resumeId: string) => void;
  onDelete: (resumeId: string) => void;
  isSettingPrimary: boolean;
  isDeleting: boolean;
}

export function ResumeCard({
  resume,
  onDownload,
  onSetPrimary,
  onDelete,
  isSettingPrimary,
  isDeleting,
}: ResumeCardProps) {
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const { checks } = useAtsResults(resume.id);
  const latestCheck = checks[0] ?? null;

  const handleDownload = async () => {
    setIsDownloading(true);
    try {
      await onDownload(resume.id);
    } finally {
      setIsDownloading(false);
    }
  };

  const handleDelete = () => {
    if (confirmDelete) {
      onDelete(resume.id);
      setConfirmDelete(false);
    } else {
      setConfirmDelete(true);
    }
  };

  return (
    <div
      className={cn(
        'flex items-center gap-4 rounded-lg border p-4 transition-colors',
        resume.is_primary
          ? 'border-blue-300 bg-blue-50/50 dark:border-blue-700 dark:bg-blue-950/20'
          : 'border-foreground/10',
      )}
    >
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-foreground/5">
        <FileText
          className={cn('h-5 w-5', resume.file_type === 'pdf' ? 'text-red-500' : 'text-blue-500')}
          aria-hidden="true"
        />
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <p className="truncate text-sm font-medium text-foreground">{resume.filename}</p>
          {resume.is_primary && (
            <span className="shrink-0 rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700 dark:bg-blue-900/50 dark:text-blue-300">
              Primary
            </span>
          )}
          {latestCheck && (
            <AtsFormatBadge score={latestCheck.format_score} />
          )}
        </div>
        <p className="text-xs text-foreground/50">
          {resume.file_type.toUpperCase()} &middot; {formatFileSize(resume.file_size)} &middot;{' '}
          {formatDate(resume.created_at)}
        </p>
      </div>

      <div className="flex shrink-0 items-center gap-1">
        {latestCheck && (
          <Button variant="ghost" size="sm" asChild>
            <Link href={`/ats?checkId=${latestCheck.id}`}>
              ATS Report
            </Link>
          </Button>
        )}
        <Button
          variant="ghost"
          size="icon"
          onClick={handleDownload}
          disabled={isDownloading}
          aria-label={`Download ${resume.filename}`}
        >
          {isDownloading ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          ) : (
            <Download className="h-4 w-4" aria-hidden="true" />
          )}
        </Button>

        {!resume.is_primary && (
          <Button
            variant="ghost"
            size="icon"
            onClick={() => onSetPrimary(resume.id)}
            disabled={isSettingPrimary}
            aria-label={`Set ${resume.filename} as primary resume`}
          >
            {isSettingPrimary ? (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            ) : (
              <Star className="h-4 w-4" aria-hidden="true" />
            )}
          </Button>
        )}

        {confirmDelete ? (
          <div className="flex items-center gap-1">
            <Button
              variant="destructive"
              size="sm"
              onClick={handleDelete}
              disabled={isDeleting}
              loading={isDeleting}
            >
              Confirm
            </Button>
            <Button variant="ghost" size="sm" onClick={() => setConfirmDelete(false)}>
              Cancel
            </Button>
          </div>
        ) : (
          <Button
            variant="ghost"
            size="icon"
            onClick={handleDelete}
            aria-label={`Delete ${resume.filename}`}
          >
            <Trash2 className="h-4 w-4 text-red-500" aria-hidden="true" />
          </Button>
        )}
      </div>
    </div>
  );
}
