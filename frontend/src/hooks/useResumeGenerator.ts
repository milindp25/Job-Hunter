"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getResumeTemplates, generateResumePdf } from "@/lib/api";
import type { ResumeTemplate } from "@/lib/types";

const TEMPLATES_QUERY_KEY = ["resume-templates"] as const;

export function useResumeGenerator() {
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    data: templatesData,
    isLoading: isLoadingTemplates,
  } = useQuery({
    queryKey: TEMPLATES_QUERY_KEY,
    queryFn: getResumeTemplates,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const templates: ResumeTemplate[] = templatesData?.templates ?? [];

  async function generate(
    resumeId: string,
    templateId: string,
    accentColor?: string,
  ): Promise<void> {
    setIsGenerating(true);
    setError(null);
    try {
      const blob = await generateResumePdf(resumeId, templateId, accentColor);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `resume_${templateId}.pdf`;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      URL.revokeObjectURL(url);
    } catch {
      setError("Failed to generate PDF. Please try again.");
    } finally {
      setIsGenerating(false);
    }
  }

  return {
    templates,
    isLoadingTemplates,
    isGenerating,
    error,
    generate,
  };
}
