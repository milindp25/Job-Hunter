interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div className={`animate-pulse rounded bg-gray-200 dark:bg-gray-700 ${className ?? ""}`} />
  );
}

export function CardSkeleton() {
  return (
    <div className="rounded-xl border border-gray-200 p-6 space-y-3 dark:border-gray-700">
      <Skeleton className="h-4 w-1/3" />
      <Skeleton className="h-8 w-1/2" />
      <Skeleton className="h-3 w-2/3" />
    </div>
  );
}
