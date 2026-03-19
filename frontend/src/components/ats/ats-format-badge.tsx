import { cn } from '@/lib/utils';

interface AtsFormatBadgeProps {
  score: number;
}

function getBadgeClass(score: number): string {
  if (score >= 80) return 'bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-400';
  if (score >= 50) return 'bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-400';
  return 'bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-400';
}

export function AtsFormatBadge({ score }: AtsFormatBadgeProps) {
  const rounded = Math.round(score);
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium tabular-nums',
        getBadgeClass(score),
      )}
      aria-label={`ATS format score: ${rounded}`}
    >
      ATS: {rounded}
    </span>
  );
}
