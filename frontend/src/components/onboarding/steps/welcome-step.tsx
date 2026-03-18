"use client";

import { useState, useCallback, useRef } from "react";
import { Upload, FileText, Linkedin, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { FormField } from "@/components/ui/form-field";
import type { OnboardingStepProps, ResumeData } from "../onboarding-types";

const ACCEPTED_TYPES = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
];
const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB

export function WelcomeStep({ data, onUpdate }: OnboardingStepProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    async (file: File) => {
      setUploadError(null);

      if (!ACCEPTED_TYPES.includes(file.type)) {
        setUploadError("Please upload a PDF or DOCX file.");
        return;
      }

      if (file.size > MAX_FILE_SIZE) {
        setUploadError("File must be smaller than 5MB.");
        return;
      }

      setIsUploading(true);
      setUploadedFile(null);

      try {
        const formData = new FormData();
        formData.append("file", file);

        const { data: parsed } = await api.post<ResumeData>(
          "/users/me/resume/parse",
          formData,
          {
            headers: { "Content-Type": "multipart/form-data" },
          },
        );

        setUploadedFile(file.name);

        // Store parsed data to pre-fill subsequent steps
        onUpdate({
          resumeData: parsed,
          personalInfo: {
            full_name: parsed.full_name ?? data.personalInfo.full_name,
            phone: parsed.phone ?? data.personalInfo.phone,
            location: parsed.location ?? data.personalInfo.location,
            linkedin_url: parsed.linkedin_url ?? data.personalInfo.linkedin_url,
            github_url: parsed.github_url ?? data.personalInfo.github_url,
            portfolio_url:
              parsed.portfolio_url ?? data.personalInfo.portfolio_url,
            summary: parsed.summary ?? data.personalInfo.summary,
          },
          skills: {
            skills:
              parsed.skills && parsed.skills.length > 0
                ? parsed.skills
                : data.skills.skills,
          },
          experience: {
            experience:
              parsed.experience && parsed.experience.length > 0
                ? parsed.experience
                : data.experience.experience,
          },
          education: {
            education:
              parsed.education && parsed.education.length > 0
                ? parsed.education
                : data.education.education,
            certifications:
              parsed.certifications && parsed.certifications.length > 0
                ? parsed.certifications
                : data.education.certifications,
          },
        });

        toast.success("Resume parsed! Fields have been pre-filled.");
      } catch {
        setUploadError("Failed to parse resume. Please try again or skip this step.");
        toast.error("Failed to parse resume. You can fill in details manually.");
      } finally {
        setIsUploading(false);
      }
    },
    [data, onUpdate],
  );

  const handleDragOver = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      e.stopPropagation();
      if (!isUploading) setIsDragging(true);
    },
    [isUploading],
  );

  const handleDragLeave = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);
    },
    [],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);

      if (isUploading) return;

      const files = e.dataTransfer.files;
      if (files.length > 0) {
        handleFile(files[0]);
      }
    },
    [isUploading, handleFile],
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        handleFile(files[0]);
      }
      // Reset the input so the same file can be re-selected
      e.target.value = "";
    },
    [handleFile],
  );

  return (
    <div className="space-y-8">
      {/* Welcome header */}
      <div className="text-center space-y-3">
        <h2 className="text-2xl font-bold text-foreground">
          Welcome to Job Hunter!
        </h2>
        <p className="text-foreground/60 max-w-lg mx-auto">
          Let&apos;s set up your profile so we can match you with the perfect
          opportunities. Upload your resume to get started quickly, or fill in
          your details manually.
        </p>
      </div>

      {/* Resume upload area */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-foreground">
          Upload your resume
        </h3>

        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => !isUploading && fileInputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              if (!isUploading) fileInputRef.current?.click();
            }
          }}
          aria-label="Upload resume file. Drag and drop or click to select. Accepts PDF and DOCX files up to 5MB."
          className={cn(
            "relative flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed p-8 transition-colors cursor-pointer",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2",
            isDragging
              ? "border-blue-500 bg-blue-50 dark:bg-blue-950/20"
              : uploadError
                ? "border-red-300 bg-red-50/50 dark:bg-red-950/10"
                : uploadedFile
                  ? "border-green-300 bg-green-50/50 dark:bg-green-950/10"
                  : "border-foreground/20 hover:border-blue-400 hover:bg-blue-50/50 dark:hover:bg-blue-950/10",
            isUploading && "pointer-events-none opacity-70",
          )}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx"
            onChange={handleFileSelect}
            className="sr-only"
            aria-hidden="true"
            tabIndex={-1}
          />

          {isUploading ? (
            <>
              <Loader2 className="h-10 w-10 text-blue-500 animate-spin" />
              <p className="text-sm font-medium text-foreground/70">
                Parsing your resume...
              </p>
            </>
          ) : uploadedFile ? (
            <>
              <CheckCircle2 className="h-10 w-10 text-green-500" />
              <div className="text-center">
                <p className="text-sm font-medium text-foreground">
                  {uploadedFile}
                </p>
                <p className="text-xs text-green-600 mt-1">
                  Successfully parsed! Click to upload a different file.
                </p>
              </div>
            </>
          ) : uploadError ? (
            <>
              <AlertCircle className="h-10 w-10 text-red-400" />
              <div className="text-center">
                <p className="text-sm text-red-600">{uploadError}</p>
                <p className="text-xs text-foreground/50 mt-1">
                  Click to try again
                </p>
              </div>
            </>
          ) : (
            <>
              <Upload className="h-10 w-10 text-foreground/40" />
              <div className="text-center">
                <p className="text-sm font-medium text-foreground/70">
                  <span className="text-blue-600">Click to upload</span> or drag
                  and drop
                </p>
                <p className="text-xs text-foreground/50 mt-1">
                  PDF or DOCX, up to 5MB
                </p>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Divider */}
      <div className="relative">
        <div className="absolute inset-0 flex items-center" aria-hidden="true">
          <div className="w-full border-t border-foreground/10" />
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="bg-background px-4 text-foreground/40">or</span>
        </div>
      </div>

      {/* LinkedIn section */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-foreground">
          Import from LinkedIn
        </h3>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <div className="flex-1">
            <FormField label="LinkedIn profile URL" htmlFor="linkedin-url">
              <Input
                id="linkedin-url"
                type="url"
                placeholder="https://linkedin.com/in/your-profile"
                value={data.linkedinUrl}
                onChange={(e) => onUpdate({ linkedinUrl: e.target.value })}
              />
            </FormField>
          </div>
          <Button
            variant="outline"
            className="shrink-0"
            onClick={() => {
              // LinkedIn OAuth would be integrated here
              toast.info("LinkedIn import will be available soon!");
            }}
          >
            <Linkedin className="h-4 w-4" />
            Connect LinkedIn
          </Button>
        </div>
      </div>

      {/* Existing resume indicator */}
      {data.resumeData && (
        <div className="flex items-center gap-2 rounded-lg bg-blue-50 p-3 text-sm text-blue-700 dark:bg-blue-950/20 dark:text-blue-300">
          <FileText className="h-4 w-4 shrink-0" />
          <span>
            Resume data has been imported. Your profile fields will be
            pre-filled in the following steps.
          </span>
        </div>
      )}

      {/* Encouraging microcopy */}
      <p className="text-center text-sm text-foreground/50">
        Great start! You can always come back and update your information later.
      </p>
    </div>
  );
}
