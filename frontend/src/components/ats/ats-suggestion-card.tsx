import { Lightbulb } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { AtsSuggestion } from '@/lib/types';

interface AtsSuggestionCardProps {
  suggestion: AtsSuggestion;
}

function impactBadgeClass(impact: string): string {
  const lower = impact.toLowerCase();
  if (lower.includes('high')) return 'bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-400';
  if (lower.includes('medium')) return 'bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-400';
  return 'bg-foreground/10 text-foreground/60';
}

export function AtsSuggestionCard({ suggestion }: AtsSuggestionCardProps) {
  return (
    <article
      className={cn(
        'relative overflow-hidden rounded-xl border border-foreground/10 bg-background shadow-sm',
        // Left gradient border accent
        'before:absolute before:inset-y-0 before:left-0 before:w-1 before:bg-gradient-to-b before:from-blue-400 before:to-indigo-500',
      )}
      aria-label={`Suggestion for ${suggestion.section} section`}
    >
      <div className="px-5 py-4 pl-6">
        {/* Header: section label + impact badge */}
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <span className="rounded-md bg-foreground/8 px-2 py-0.5 text-xs font-semibold uppercase tracking-wide text-foreground/60">
            {suggestion.section}
          </span>
          <span
            className={cn(
              'rounded-full px-2 py-0.5 text-xs font-medium',
              impactBadgeClass(suggestion.estimated_impact),
            )}
          >
            {suggestion.estimated_impact} impact
          </span>
        </div>

        {/* Before / After diff */}
        <div className="space-y-2">
          {/* Before */}
          <div className="rounded-md bg-red-50 px-3 py-2 dark:bg-red-950/20">
            <div className="mb-1 flex items-center gap-1">
              <span className="text-xs font-bold text-red-600 dark:text-red-400">-</span>
              <span className="text-xs font-semibold text-red-600 dark:text-red-400">Before</span>
            </div>
            <p className="text-sm text-red-800 dark:text-red-300">{suggestion.before}</p>
          </div>

          {/* After */}
          <div className="rounded-md bg-green-50 px-3 py-2 dark:bg-green-950/20">
            <div className="mb-1 flex items-center gap-1">
              <span className="text-xs font-bold text-green-600 dark:text-green-400">+</span>
              <span className="text-xs font-semibold text-green-600 dark:text-green-400">After</span>
            </div>
            <p className="text-sm text-green-800 dark:text-green-300">{suggestion.after}</p>
          </div>
        </div>

        {/* Reason */}
        <div className="mt-3 flex items-start gap-2 text-foreground/60">
          <Lightbulb className="mt-0.5 h-4 w-4 shrink-0 text-amber-500" aria-hidden="true" />
          <p className="text-xs">{suggestion.reason}</p>
        </div>
      </div>
    </article>
  );
}
