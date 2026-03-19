interface AtsKeywordBarProps {
  matched: number;
  missing: number;
  total: number;
}

export function AtsKeywordBar({ matched, missing, total }: AtsKeywordBarProps) {
  const matchedPct = total > 0 ? Math.round((matched / total) * 100) : 0;
  const missingPct = total > 0 ? Math.round((missing / total) * 100) : 0;

  return (
    <div className="w-full space-y-1.5">
      {/* Bar */}
      <div
        className="flex h-3 w-full overflow-hidden rounded-full bg-foreground/10"
        role="img"
        aria-label={`Keyword coverage: ${matched} of ${total} matched (${matchedPct}%)`}
      >
        {matched > 0 && (
          <div
            className="h-full bg-green-500 transition-all duration-500"
            style={{ width: `${matchedPct}%` }}
          />
        )}
        {missing > 0 && (
          <div
            className="h-full bg-red-400 transition-all duration-500"
            style={{ width: `${missingPct}%` }}
          />
        )}
      </div>

      {/* Labels */}
      <div className="flex justify-between text-xs text-foreground/50">
        <span className="flex items-center gap-1">
          <span className="inline-block h-2 w-2 rounded-full bg-green-500" aria-hidden="true" />
          {matched} matched
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-2 w-2 rounded-full bg-red-400" aria-hidden="true" />
          {missing} missing
        </span>
        <span>{total} total</span>
      </div>
    </div>
  );
}
