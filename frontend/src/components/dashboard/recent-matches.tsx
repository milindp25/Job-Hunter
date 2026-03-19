"use client";

import { Target } from "lucide-react";
import { formatRelativeTime } from "@/lib/utils";
import type { RecentMatch } from "@/lib/types";

interface RecentMatchesProps {
  matches: RecentMatch[];
}

function ScoreBadge({ score }: { score: number }) {
  const color =
    score >= 80
      ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
      : score >= 60
        ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400"
        : "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400";

  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${color}`}>
      {score}%
    </span>
  );
}

export function RecentMatches({ matches }: RecentMatchesProps) {
  return (
    <div className="rounded-xl border border-foreground/10 bg-background p-6 shadow-sm">
      <h3 className="mb-4 text-sm font-semibold text-foreground">
        Recent Matches
      </h3>

      {matches.length === 0 ? (
        <div className="flex h-32 flex-col items-center justify-center gap-2 text-foreground/40">
          <Target className="h-8 w-8" />
          <p className="text-sm">No matches yet. Complete your profile to get started!</p>
        </div>
      ) : (
        <ul className="space-y-3">
          {matches.map((match, index) => (
            <li
              key={`${match.job_title}-${index}`}
              className="flex items-center justify-between rounded-lg border border-foreground/5 px-4 py-3 transition-colors hover:bg-foreground/[0.02]"
            >
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-foreground">
                  {match.job_title}
                </p>
                <p className="text-xs text-foreground/50">{match.company}</p>
              </div>
              <div className="ml-4 flex items-center gap-3">
                <ScoreBadge score={match.score} />
                {match.matched_at && (
                  <span className="text-xs text-foreground/40">
                    {formatRelativeTime(match.matched_at)}
                  </span>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
