"use client";

import { use, useState, useCallback } from "react";
import Link from "next/link";
import { ArrowLeft, Download, Loader2, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { AuthGuard } from "@/components/layout/auth-guard";
import { TailorDiffView } from "@/components/tailor/tailor-diff-view";
import { KeywordAnalysis } from "@/components/tailor/keyword-analysis";
import { useTailoredResume } from "@/hooks/useTailoredResume";
import { generateResumePdf } from "@/lib/api";

const TEMPLATES = [
  { id: "classic", label: "Classic" },
  { id: "modern", label: "Modern" },
  { id: "minimal", label: "Minimal" },
] as const;

interface TailorResultPageProps {
  params: Promise<{ id: string }>;
}

export default function TailorResultPage({ params }: TailorResultPageProps) {
  const { id } = use(params);

  return (
    <AuthGuard>
      <TailorResultContent id={id} />
    </AuthGuard>
  );
}

function TailorResultContent({ id }: { id: string }) {
  const { data: tailored, isLoading, error } = useTailoredResume(
    id === "0" ? null : id,
  );
  const [selectedTemplate, setSelectedTemplate] = useState<string>("classic");
  const [isDownloading, setIsDownloading] = useState(false);

  const handleDownloadPdf = useCallback(async () => {
    if (!tailored) return;
    setIsDownloading(true);
    try {
      const blob = await generateResumePdf(tailored.resume_id, selectedTemplate);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `tailored-resume-${selectedTemplate}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch {
      toast.error("Failed to generate PDF. Please try again.");
    } finally {
      setIsDownloading(false);
    }
  }, [tailored, selectedTemplate]);

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (error || !tailored) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-12 text-center">
        <h1 className="text-xl font-bold text-foreground">
          Tailored resume not found
        </h1>
        <p className="mt-2 text-foreground/60">
          The tailored resume you are looking for does not exist or you do not
          have access.
        </p>
        <Button asChild className="mt-6">
          <Link href="/dashboard">Back to Dashboard</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" asChild>
            <Link href="/dashboard" aria-label="Back to dashboard">
              <ArrowLeft className="h-5 w-5" />
            </Link>
          </Button>
          <div>
            <h1 className="flex items-center gap-2 text-2xl font-bold text-foreground">
              <Sparkles className="h-6 w-6 text-blue-600" />
              Tailored Resume
            </h1>
            <p className="mt-1 text-sm text-foreground/60">
              AI-optimized for job #{tailored.job_id}
            </p>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="grid gap-8 lg:grid-cols-[1fr_300px]">
        <div>
          <TailorDiffView tailored={tailored} />
        </div>

        {/* Sidebar */}
        <aside className="space-y-6">
          <div className="sticky top-24 space-y-6">
            <div className="rounded-xl border border-foreground/10 bg-background p-6 shadow-sm">
              <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold text-foreground">
                <Sparkles className="h-4 w-4 text-blue-600" />
                Keyword Analysis
              </h2>
              <KeywordAnalysis tailored={tailored} />
            </div>

            {/* PDF Download */}
            <div className="rounded-xl border border-foreground/10 bg-background p-6 shadow-sm">
              <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold text-foreground">
                <Download className="h-4 w-4 text-blue-600" />
                Download PDF
              </h2>

              <fieldset className="mb-4 space-y-2">
                <legend className="mb-1 text-xs font-medium text-foreground/60">
                  Template
                </legend>
                {TEMPLATES.map((tmpl) => (
                  <label
                    key={tmpl.id}
                    className="flex cursor-pointer items-center gap-2 text-sm text-foreground"
                  >
                    <input
                      type="radio"
                      name="pdf-template"
                      value={tmpl.id}
                      checked={selectedTemplate === tmpl.id}
                      onChange={() => setSelectedTemplate(tmpl.id)}
                      className="accent-blue-600"
                    />
                    {tmpl.label}
                  </label>
                ))}
              </fieldset>

              <Button
                onClick={handleDownloadPdf}
                disabled={isDownloading}
                className="w-full"
              >
                {isDownloading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Download className="mr-2 h-4 w-4" />
                    Download PDF
                  </>
                )}
              </Button>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
