import type { TailoredResume } from "@/lib/types";

interface KeywordAnalysisProps {
  tailored: TailoredResume;
}

export function KeywordAnalysis({ tailored }: KeywordAnalysisProps) {
  return (
    <div className="space-y-6">
      {/* Score Badges */}
      <div className="flex items-center gap-3">
        <div className="rounded-lg bg-foreground/5 px-3 py-2 text-center">
          <p className="text-xs text-foreground/60">Before</p>
          <p className="text-lg font-bold text-foreground">
            {tailored.match_score_before ?? 0}%
          </p>
        </div>
        <span className="text-foreground/40" aria-hidden="true">
          &rarr;
        </span>
        <div className="rounded-lg bg-green-50 px-3 py-2 text-center dark:bg-green-950">
          <p className="text-xs text-green-700 dark:text-green-300">After</p>
          <p className="text-lg font-bold text-green-700 dark:text-green-300">
            {tailored.match_score_after ?? 0}%
          </p>
        </div>
      </div>

      {/* Matched Keywords */}
      {tailored.keyword_matches.length > 0 && (
        <div>
          <h3 className="mb-2 text-sm font-semibold text-foreground">
            Matched Keywords
          </h3>
          <div className="flex flex-wrap gap-1.5">
            {tailored.keyword_matches.map((kw) => (
              <span
                key={kw}
                className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800 dark:bg-green-900 dark:text-green-200"
              >
                {kw}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Gap Keywords */}
      {tailored.keyword_gaps.length > 0 && (
        <div>
          <h3 className="mb-2 text-sm font-semibold text-foreground">
            Missing Keywords
          </h3>
          <div className="flex flex-wrap gap-1.5">
            {tailored.keyword_gaps.map((kw) => (
              <span
                key={kw}
                className="inline-flex items-center rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-medium text-red-800 dark:bg-red-900 dark:text-red-200"
              >
                {kw}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* AI Model Info */}
      <div className="border-t border-foreground/10 pt-4">
        <p className="text-xs text-foreground/50">
          Powered by {tailored.ai_model}
        </p>
      </div>
    </div>
  );
}
