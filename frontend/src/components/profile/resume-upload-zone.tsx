'use client';

import { useState, useCallback, useRef } from 'react';
import { Upload, Loader2, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

const ACCEPTED_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
];
const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB

interface ResumeUploadZoneProps {
  onFileSelected: (file: File) => void;
  isUploading: boolean;
}

export function ResumeUploadZone({ onFileSelected, isUploading }: ResumeUploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateAndSubmit = useCallback(
    (file: File) => {
      setValidationError(null);

      if (!ACCEPTED_TYPES.includes(file.type)) {
        setValidationError('Please upload a PDF or DOCX file.');
        return;
      }

      if (file.size > MAX_FILE_SIZE) {
        setValidationError('File must be smaller than 5MB.');
        return;
      }

      onFileSelected(file);
    },
    [onFileSelected],
  );

  const handleDragOver = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      e.stopPropagation();
      if (!isUploading) setIsDragging(true);
    },
    [isUploading],
  );

  const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);

      if (isUploading) return;

      const files = e.dataTransfer.files;
      if (files.length > 0) {
        validateAndSubmit(files[0]);
      }
    },
    [isUploading, validateAndSubmit],
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        validateAndSubmit(files[0]);
      }
      e.target.value = '';
    },
    [validateAndSubmit],
  );

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => !isUploading && fileInputRef.current?.click()}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          if (!isUploading) fileInputRef.current?.click();
        }
      }}
      aria-label="Upload resume file. Drag and drop or click to select. Accepts PDF and DOCX files up to 5MB."
      className={cn(
        'relative flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed p-8 transition-colors cursor-pointer',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2',
        isDragging
          ? 'border-blue-500 bg-blue-50 dark:bg-blue-950/20'
          : validationError
            ? 'border-red-300 bg-red-50/50 dark:bg-red-950/10'
            : 'border-foreground/20 hover:border-blue-400 hover:bg-blue-50/50 dark:hover:bg-blue-950/10',
        isUploading && 'pointer-events-none opacity-70',
      )}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.docx"
        onChange={handleFileSelect}
        className="sr-only"
        aria-hidden="true"
        tabIndex={-1}
      />

      {isUploading ? (
        <>
          <Loader2 className="h-10 w-10 text-blue-500 animate-spin" />
          <p className="text-sm font-medium text-foreground/70">Uploading resume...</p>
        </>
      ) : validationError ? (
        <>
          <AlertCircle className="h-10 w-10 text-red-400" />
          <div className="text-center">
            <p className="text-sm text-red-600">{validationError}</p>
            <p className="text-xs text-foreground/50 mt-1">Click to try again</p>
          </div>
        </>
      ) : (
        <>
          <Upload className="h-10 w-10 text-foreground/40" />
          <div className="text-center">
            <p className="text-sm font-medium text-foreground/70">
              <span className="text-blue-600">Click to upload</span> or drag and drop
            </p>
            <p className="text-xs text-foreground/50 mt-1">PDF or DOCX, up to 5MB</p>
          </div>
        </>
      )}
    </div>
  );
}
