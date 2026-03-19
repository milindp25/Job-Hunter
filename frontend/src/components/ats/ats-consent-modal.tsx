'use client';

import { useEffect } from 'react';
import { ShieldCheck, X } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface AtsConsentModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConsented: () => void;
}

export function AtsConsentModal({ open, onOpenChange, onConsented }: AtsConsentModalProps) {
  // Close on Escape key
  useEffect(() => {
    if (!open) return;
    function handleKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onOpenChange(false);
    }
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [open, onOpenChange]);

  // Trap body scroll
  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [open]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="ats-consent-title"
      aria-describedby="ats-consent-desc"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={() => onOpenChange(false)}
        aria-hidden="true"
      />

      {/* Dialog */}
      <div className="relative w-full max-w-md rounded-2xl border border-foreground/10 bg-background p-6 shadow-xl">
        {/* Close button */}
        <button
          type="button"
          className="absolute right-4 top-4 rounded-md p-1 text-foreground/40 hover:bg-foreground/5 hover:text-foreground/70"
          onClick={() => onOpenChange(false)}
          aria-label="Close dialog"
        >
          <X className="h-4 w-4" />
        </button>

        {/* Icon + Title */}
        <div className="mb-4 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-950/40">
            <ShieldCheck className="h-5 w-5 text-blue-600 dark:text-blue-400" aria-hidden="true" />
          </div>
          <h2 id="ats-consent-title" className="text-base font-semibold text-foreground">
            AI-Powered Analysis
          </h2>
        </div>

        {/* Body */}
        <p id="ats-consent-desc" className="text-sm text-foreground/70">
          To run a full ATS compliance check with keyword and content analysis, we use{' '}
          <strong className="text-foreground">Google Gemini 2.0 Flash</strong>. This requires
          sending your resume text and (if provided) the job description to Google&apos;s API.
        </p>

        <ul className="mt-3 space-y-1.5 text-sm text-foreground/60">
          <li className="flex items-start gap-2">
            <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-foreground/30" aria-hidden="true" />
            Resume text is sent to Google for analysis only — not stored by Google.
          </li>
          <li className="flex items-start gap-2">
            <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-foreground/30" aria-hidden="true" />
            Format checking runs locally and does not require AI consent.
          </li>
          <li className="flex items-start gap-2">
            <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-foreground/30" aria-hidden="true" />
            Your consent is saved so you won&apos;t be asked again.
          </li>
        </ul>

        {/* Actions */}
        <div className="mt-6 flex gap-3">
          <Button
            variant="outline"
            className="flex-1"
            onClick={() => onOpenChange(false)}
          >
            Decline
          </Button>
          <Button
            className="flex-1"
            onClick={() => {
              onConsented();
              onOpenChange(false);
            }}
          >
            Accept &amp; Continue
          </Button>
        </div>
      </div>
    </div>
  );
}
