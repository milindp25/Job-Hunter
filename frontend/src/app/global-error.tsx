"use client";

export default function GlobalError({
  error,
  unstable_retry,
}: {
  error: Error & { digest?: string };
  unstable_retry: () => void;
}) {
  return (
    <html lang="en">
      <body className="bg-slate-950 text-white">
        <div className="flex min-h-screen flex-col items-center justify-center gap-6 px-4">
          <h2 className="text-2xl font-bold">Something went wrong</h2>
          <p className="text-slate-400">
            A critical error occurred. Please try again.
          </p>
          {error.digest && (
            <p className="text-sm text-slate-500">Error ID: {error.digest}</p>
          )}
          <button
            onClick={() => unstable_retry()}
            className="rounded-lg bg-blue-600 px-6 py-2 text-white hover:bg-blue-700"
          >
            Try Again
          </button>
        </div>
      </body>
    </html>
  );
}
