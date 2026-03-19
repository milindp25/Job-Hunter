'use client';

import { useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { ShieldCheck, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { api } from '@/lib/api';

interface AtsConsentModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConsented: () => void;
}

export function AtsConsentModal({ open, onOpenChange, onConsented }: AtsConsentModalProps) {
  const [accepting, setAccepting] = useState(false);
  const [error, setError] = useState(false);

  async function handleAccept() {
    setAccepting(true);
    setError(false);
    try {
      await api.patch('/users/profile', { ai_analysis_consented: true });
      onConsented();
      onOpenChange(false);
    } catch {
      setAccepting(false);
      setError(true);
    }
  }

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=open]:fade-in-0 data-[state=closed]:fade-out-0" />
        <Dialog.Content
          className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-2xl border border-foreground/10 bg-background p-6 shadow-xl focus:outline-none data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=open]:fade-in-0 data-[state=closed]:fade-out-0 data-[state=open]:zoom-in-95 data-[state=closed]:zoom-out-95"
          aria-describedby="ats-consent-desc"
        >
          {/* Close button */}
          <Dialog.Close asChild>
            <button
              type="button"
              className="absolute right-4 top-4 rounded-md p-1 text-foreground/40 hover:bg-foreground/5 hover:text-foreground/70"
              aria-label="Close dialog"
            >
              <X className="h-4 w-4" />
            </button>
          </Dialog.Close>

          {/* Icon + Title */}
          <div className="mb-4 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-950/40">
              <ShieldCheck className="h-5 w-5 text-blue-600 dark:text-blue-400" aria-hidden="true" />
            </div>
            <Dialog.Title className="text-base font-semibold text-foreground">
              AI-Powered Analysis
            </Dialog.Title>
          </div>

          {/* Body */}
          <Dialog.Description id="ats-consent-desc" className="text-sm text-foreground/70">
            To run a full ATS compliance check with keyword and content analysis, we use{' '}
            <strong className="text-foreground">Google Gemini 2.0 Flash</strong>. This requires
            sending your resume text and (if provided) the job description to Google&apos;s API.
          </Dialog.Description>

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

          {/* Error feedback */}
          {error && (
            <p className="mt-4 text-sm text-red-600 dark:text-red-400" role="alert">
              Failed to save consent. Please try again.
            </p>
          )}

          {/* Actions */}
          <div className="mt-6 flex gap-3">
            <Dialog.Close asChild>
              <Button variant="outline" className="flex-1">
                Decline
              </Button>
            </Dialog.Close>
            <Button
              className="flex-1"
              disabled={accepting}
              onClick={handleAccept}
            >
              {accepting ? 'Saving…' : 'Accept & Continue'}
            </Button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
