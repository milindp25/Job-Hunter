import { cn } from '@/lib/utils';

interface AtsScoreHeaderProps {
  overallScore: number;
  formatScore: number;
  keywordScore: number | null;
  contentScore: number | null;
}

function getScoreColor(score: number): string {
  if (score >= 80) return 'text-green-600 dark:text-green-400';
  if (score >= 50) return 'text-amber-600 dark:text-amber-400';
  return 'text-red-600 dark:text-red-400';
}

function getScoreStroke(score: number): string {
  if (score >= 80) return 'stroke-green-500';
  if (score >= 50) return 'stroke-amber-500';
  return 'stroke-red-500';
}

function getScoreBg(score: number): string {
  if (score >= 80) return 'bg-green-50 dark:bg-green-950/30 border-green-200 dark:border-green-800';
  if (score >= 50) return 'bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-800';
  return 'bg-red-50 dark:bg-red-950/30 border-red-200 dark:border-red-800';
}

interface CircleProgressProps {
  score: number;
  size: 'lg' | 'sm';
  label: string;
}

function CircleProgress({ score, size, label }: CircleProgressProps) {
  const dimension = size === 'lg' ? 80 : 64;
  const radius = size === 'lg' ? 34 : 26;
  const strokeWidth = size === 'lg' ? 6 : 5;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const center = dimension / 2;
  const fontSize = size === 'lg' ? 'text-xl' : 'text-sm';

  return (
    <div className="relative flex items-center justify-center" style={{ width: dimension, height: dimension }}>
      <svg
        width={dimension}
        height={dimension}
        viewBox={`0 0 ${dimension} ${dimension}`}
        aria-hidden="true"
        className="-rotate-90"
      >
        {/* Track */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-foreground/10"
        />
        {/* Progress */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className={cn('transition-all duration-700 ease-out', getScoreStroke(score))}
        />
      </svg>
      <span
        className={cn(
          'absolute font-bold tabular-nums',
          fontSize,
          getScoreColor(score),
        )}
        aria-label={label}
      >
        {score}
      </span>
    </div>
  );
}

interface SubScoreCardProps {
  label: string;
  score: number | null;
  description?: string;
}

function SubScoreCard({ label, score, description }: SubScoreCardProps) {
  if (score === null) {
    return (
      <div className="flex flex-col items-center gap-2 rounded-xl border border-foreground/10 bg-foreground/3 p-4 opacity-50">
        <div
          className="flex h-16 w-16 items-center justify-center rounded-full border-2 border-dashed border-foreground/20"
          aria-label={`${label}: not available`}
        >
          <span className="text-xs text-foreground/40">N/A</span>
        </div>
        <span className="text-xs font-medium text-foreground/50">{label}</span>
        {description && <span className="text-center text-xs text-foreground/30">{description}</span>}
      </div>
    );
  }

  return (
    <div
      className={cn(
        'flex flex-col items-center gap-2 rounded-xl border p-4',
        getScoreBg(score),
      )}
    >
      <CircleProgress score={score} size="sm" label={`${label}: ${score}`} />
      <span className={cn('text-xs font-medium', getScoreColor(score))}>{label}</span>
      {description && <span className="text-center text-xs text-foreground/50">{description}</span>}
    </div>
  );
}

export function AtsScoreHeader({
  overallScore,
  formatScore,
  keywordScore,
  contentScore,
}: AtsScoreHeaderProps) {
  return (
    <div className="flex flex-col items-center gap-6 sm:flex-row sm:items-start">
      {/* Overall score — large card */}
      <div
        className={cn(
          'flex min-w-[180px] flex-col items-center gap-3 rounded-2xl border-2 p-6 shadow-sm',
          getScoreBg(overallScore),
        )}
      >
        <CircleProgress score={overallScore} size="lg" label={`Overall ATS score: ${overallScore}`} />
        <div className="text-center">
          <p className={cn('text-lg font-bold', getScoreColor(overallScore))}>
            {overallScore >= 80 ? 'Excellent' : overallScore >= 50 ? 'Needs Work' : 'At Risk'}
          </p>
          <p className="mt-0.5 text-xs text-foreground/50">Overall ATS Score</p>
        </div>
        <p className="mt-1 text-center text-xs text-foreground/40">
          = avg(format, keyword, content)
        </p>
      </div>

      {/* Sub-scores */}
      <div className="grid flex-1 grid-cols-3 gap-3">
        <SubScoreCard
          label="Format"
          score={formatScore}
          description="Parsing compatibility"
        />
        <SubScoreCard
          label="Keywords"
          score={keywordScore}
          description="Job keyword match"
        />
        <SubScoreCard
          label="Content"
          score={contentScore}
          description="AI content quality"
        />
      </div>
    </div>
  );
}
