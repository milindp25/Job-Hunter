'use client';

import { Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MatchScoreBadgeProps {
  score: number;
  size?: 'sm' | 'md';
}

function getScoreColor(score: number): string {
  if (score >= 80) return 'bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-400';
  if (score >= 60) return 'bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-400';
  if (score >= 40) return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-950 dark:text-yellow-400';
  return 'bg-foreground/5 text-foreground/50';
}

export function MatchScoreBadge({ score, size = 'sm' }: MatchScoreBadgeProps) {
  const rounded = Math.round(score);

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full font-medium',
        getScoreColor(score),
        size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm',
      )}
      aria-label={`Match score: ${rounded}%`}
    >
      <Sparkles className={cn(size === 'sm' ? 'h-3 w-3' : 'h-4 w-4')} />
      {rounded}%
    </span>
  );
}
