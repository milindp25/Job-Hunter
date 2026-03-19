import { AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface AtsStaleBannerProps {
  isStale: boolean;
  onRerun: () => void;
}

export function AtsStaleBanner({ isStale, onRerun }: AtsStaleBannerProps) {
  if (!isStale) return null;

  return (
    <div
      role="alert"
      className="flex flex-col gap-3 rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 dark:border-amber-700 dark:bg-amber-950/30 sm:flex-row sm:items-center sm:justify-between"
    >
      <div className="flex items-start gap-2.5 sm:items-center">
        <AlertTriangle
          className="mt-0.5 h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400 sm:mt-0"
          aria-hidden="true"
        />
        <p className="text-sm font-medium text-amber-800 dark:text-amber-300">
          This report may be out of date. Your resume or the job description has changed since this
          check was run.
        </p>
      </div>
      <Button
        variant="outline"
        size="sm"
        onClick={onRerun}
        className="shrink-0 border-amber-400 text-amber-700 hover:bg-amber-100 dark:border-amber-600 dark:text-amber-300 dark:hover:bg-amber-900/30"
      >
        Re-run Check
      </Button>
    </div>
  );
}
