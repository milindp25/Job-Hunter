'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { AtsFinding } from '@/lib/types';

interface AtsFindingsSectionProps {
  category: string;
  title: string;
  icon: React.ReactNode;
  score: number | null;
  findings: AtsFinding[];
  onDismiss: (findingId: string, dismissed: boolean) => void;
}

function severityDotClass(severity: AtsFinding['severity']): string {
  switch (severity) {
    case 'blocker':
      return 'bg-red-600';
    case 'critical':
      return 'bg-orange-500';
    case 'warning':
      return 'bg-amber-500';
    case 'info':
      return 'bg-blue-400';
  }
}

function severityLabel(severity: AtsFinding['severity']): string {
  switch (severity) {
    case 'blocker':
      return 'Blocker';
    case 'critical':
      return 'Critical';
    case 'warning':
      return 'Warning';
    case 'info':
      return 'Info';
  }
}

function confidenceBadgeClass(confidence: AtsFinding['confidence']): string {
  switch (confidence) {
    case 'high':
      return 'bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-400';
    case 'medium':
      return 'bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-400';
    case 'low':
      return 'bg-foreground/10 text-foreground/50';
  }
}

interface FindingRowProps {
  finding: AtsFinding;
  onDismiss: (findingId: string, dismissed: boolean) => void;
}

function FindingRow({ finding, onDismiss }: FindingRowProps) {
  const [suggestionOpen, setSuggestionOpen] = useState(false);

  return (
    <li
      className={cn(
        'rounded-lg border px-4 py-3 transition-opacity',
        finding.dismissed
          ? 'border-foreground/10 bg-foreground/3 opacity-50'
          : 'border-foreground/10 bg-background',
      )}
    >
      <div className="flex items-start gap-3">
        {/* Severity dot */}
        <span
          className={cn('mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full', severityDotClass(finding.severity))}
          title={severityLabel(finding.severity)}
          aria-label={`Severity: ${severityLabel(finding.severity)}`}
        />

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={cn(
                'text-sm font-semibold',
                finding.dismissed ? 'line-through text-foreground/40' : 'text-foreground',
              )}
            >
              {finding.title}
            </span>
            <span
              className={cn(
                'rounded-full px-2 py-0.5 text-xs font-medium',
                confidenceBadgeClass(finding.confidence),
              )}
            >
              {finding.confidence} confidence
            </span>
          </div>

          <p className="mt-1 text-sm text-foreground/60">{finding.detail}</p>

          {/* Collapsible suggestion */}
          {finding.suggestion && !finding.dismissed && (
            <div className="mt-2">
              <button
                type="button"
                className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400"
                onClick={() => setSuggestionOpen((prev) => !prev)}
                aria-expanded={suggestionOpen}
              >
                {suggestionOpen ? (
                  <>
                    <ChevronUp className="h-3 w-3" />
                    Hide suggestion
                  </>
                ) : (
                  <>
                    <ChevronDown className="h-3 w-3" />
                    Show suggestion
                  </>
                )}
              </button>
              {suggestionOpen && (
                <p className="mt-1.5 rounded-md bg-blue-50 px-3 py-2 text-xs text-blue-800 dark:bg-blue-950/30 dark:text-blue-300">
                  {finding.suggestion}
                </p>
              )}
            </div>
          )}
        </div>

        {/* Dismiss / Restore button */}
        <button
          type="button"
          onClick={() => onDismiss(finding.id, !finding.dismissed)}
          className={cn(
            'shrink-0 rounded px-2 py-1 text-xs font-medium transition-colors',
            finding.dismissed
              ? 'text-blue-600 hover:bg-blue-50 dark:text-blue-400 dark:hover:bg-blue-950/30'
              : 'text-foreground/40 hover:bg-foreground/5 hover:text-foreground/70',
          )}
          aria-label={finding.dismissed ? 'Restore finding' : 'Dismiss finding'}
        >
          {finding.dismissed ? 'Restore' : 'Dismiss'}
        </button>
      </div>
    </li>
  );
}

function getScoreColor(score: number): string {
  if (score >= 80) return 'text-green-600 dark:text-green-400';
  if (score >= 50) return 'text-amber-600 dark:text-amber-400';
  return 'text-red-600 dark:text-red-400';
}

export function AtsFindingsSection({
  category,
  title,
  icon,
  score,
  findings,
  onDismiss,
}: AtsFindingsSectionProps) {
  const active = findings.filter((f) => !f.dismissed);
  const dismissed = findings.filter((f) => f.dismissed);

  return (
    <section aria-label={`${title} findings`} className="space-y-3">
      {/* Section header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-foreground/60" aria-hidden="true">
            {icon}
          </span>
          <h2 className="text-base font-semibold text-foreground">{title}</h2>
          {findings.length > 0 && (
            <span className="rounded-full bg-foreground/10 px-2 py-0.5 text-xs font-medium text-foreground/60">
              {active.length} active
            </span>
          )}
        </div>
        {score !== null && (
          <span className={cn('text-sm font-bold tabular-nums', getScoreColor(score))}>
            {score}/100
          </span>
        )}
      </div>

      {findings.length === 0 ? (
        <p className="rounded-lg border border-foreground/10 bg-foreground/3 px-4 py-3 text-sm text-foreground/40">
          No {category} findings — looks good!
        </p>
      ) : (
        <ul className="space-y-2">
          {active.map((f) => (
            <FindingRow key={f.id} finding={f} onDismiss={onDismiss} />
          ))}
          {dismissed.map((f) => (
            <FindingRow key={f.id} finding={f} onDismiss={onDismiss} />
          ))}
        </ul>
      )}
    </section>
  );
}
