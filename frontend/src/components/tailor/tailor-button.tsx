"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Sparkles, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTailorResume } from "@/hooks/useTailoredResume";

interface TailorButtonProps {
  resumeId: string;
  jobId: string;
  className?: string;
}

export function TailorButton({ resumeId, jobId, className }: TailorButtonProps) {
  const router = useRouter();
  const tailorMutation = useTailorResume();
  const [error, setError] = useState<string | null>(null);

  async function handleTailor() {
    setError(null);
    try {
      const result = await tailorMutation.mutateAsync({ resumeId, jobId });
      router.push(`/tailor/${result.id}`);
    } catch {
      setError("Failed to tailor resume. Please try again.");
    }
  }

  return (
    <div className={className}>
      <Button
        onClick={handleTailor}
        disabled={tailorMutation.isPending}
        variant="default"
        size="sm"
      >
        {tailorMutation.isPending ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            Tailoring...
          </>
        ) : (
          <>
            <Sparkles className="h-4 w-4" aria-hidden="true" />
            Tailor Resume
          </>
        )}
      </Button>
      {error && (
        <p className="mt-1 text-xs text-red-600" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
