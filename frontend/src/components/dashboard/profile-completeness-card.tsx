"use client";

import * as Progress from "@radix-ui/react-progress";
import { cn } from "@/lib/utils";

interface ProfileCompletenessCardProps {
  completeness: number;
}

function getCompletenessColor(value: number): string {
  if (value >= 80) return "bg-green-500";
  if (value >= 50) return "bg-yellow-500";
  return "bg-red-500";
}

function getCompletenessLabel(value: number): string {
  if (value >= 80) return "Great progress!";
  if (value >= 50) return "Getting there";
  return "Just getting started";
}

export function ProfileCompletenessCard({
  completeness,
}: ProfileCompletenessCardProps) {
  return (
    <div className="rounded-xl border border-foreground/10 bg-background p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-foreground/70">
          Profile Completeness
        </h3>
        <span className="text-2xl font-bold text-foreground">
          {completeness}%
        </span>
      </div>
      <Progress.Root
        className="mt-3 h-2.5 overflow-hidden rounded-full bg-foreground/10"
        value={completeness}
        aria-label={`Profile ${completeness}% complete`}
      >
        <Progress.Indicator
          className={cn(
            "h-full rounded-full transition-all duration-500",
            getCompletenessColor(completeness),
          )}
          style={{ width: `${completeness}%` }}
        />
      </Progress.Root>
      <p className="mt-2 text-sm text-foreground/60">
        {getCompletenessLabel(completeness)}
      </p>
    </div>
  );
}
