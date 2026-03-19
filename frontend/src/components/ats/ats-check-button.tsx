'use client';

import { useState } from 'react';
import { ScanLine } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { AtsConsentModal } from './ats-consent-modal';
import { useRunAtsCheck } from '@/hooks/useAtsCheck';
import type { AtsCheck } from '@/lib/types';

interface AtsCheckButtonProps {
  resumeId: string;
  jobId?: string;
  onSuccess?: (check: AtsCheck) => void;
}

function isConsentRequiredError(err: unknown): boolean {
  if (!err || typeof err !== 'object') return false;
  const e = err as Record<string, unknown>;
  // Axios errors have response.status and response.data
  if ('response' in e && e.response && typeof e.response === 'object') {
    const res = e.response as Record<string, unknown>;
    if (res.status === 403) {
      const data = res.data as Record<string, unknown> | null;
      if (data && typeof data === 'object' && 'error' in data) {
        const error = data.error as Record<string, unknown>;
        return error.code === 'ATS_CONSENT_REQUIRED';
      }
    }
  }
  return false;
}

export function AtsCheckButton({ resumeId, jobId, onSuccess }: AtsCheckButtonProps) {
  const { mutate, isPending } = useRunAtsCheck();
  const [consentOpen, setConsentOpen] = useState(false);

  function runCheck() {
    mutate(
      { resumeId, jobId },
      {
        onSuccess: (check) => {
          onSuccess?.(check);
        },
        onError: (err) => {
          if (isConsentRequiredError(err)) {
            setConsentOpen(true);
          }
        },
      },
    );
  }

  function handleConsented() {
    // Re-run after consent is stored on the server via the accept endpoint.
    // For simplicity we trigger the check again; the backend will see consent now.
    runCheck();
  }

  return (
    <>
      <Button onClick={runCheck} loading={isPending} disabled={isPending}>
        <ScanLine className="h-4 w-4" aria-hidden="true" />
        {isPending ? 'Checking…' : 'Run ATS Check'}
      </Button>

      <AtsConsentModal
        open={consentOpen}
        onOpenChange={setConsentOpen}
        onConsented={handleConsented}
      />
    </>
  );
}
