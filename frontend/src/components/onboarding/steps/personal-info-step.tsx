"use client";

import { useEffect, useMemo } from "react";
import { useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { FormField } from "@/components/ui/form-field";
import type { OnboardingStepProps, PersonalInfoData } from "../onboarding-types";

const urlOrEmpty = z.union([
  z.string().url("Please enter a valid URL"),
  z.literal(""),
]);

const personalInfoSchema = z.object({
  full_name: z.string().min(1, "Full name is required"),
  phone: z.string(),
  location: z.string(),
  linkedin_url: urlOrEmpty,
  github_url: urlOrEmpty,
  portfolio_url: urlOrEmpty,
  summary: z.string(),
});

type PersonalInfoFormValues = z.infer<typeof personalInfoSchema>;

function AutoFilledBadge() {
  return (
    <span className="inline-flex items-center gap-1 rounded-md bg-blue-100 px-1.5 py-0.5 text-xs text-blue-700 dark:bg-blue-900/40 dark:text-blue-300">
      <Sparkles className="h-3 w-3" />
      Auto-filled from resume
    </span>
  );
}

export function PersonalInfoStep({
  data,
  onUpdate,
  resumeData,
}: OnboardingStepProps) {
  // Track which fields were auto-filled from resume
  const autoFilledFields = useMemo(() => {
    const fields = new Set<string>();
    if (!resumeData) return fields;

    if (resumeData.full_name) fields.add("full_name");
    if (resumeData.phone) fields.add("phone");
    if (resumeData.location) fields.add("location");
    if (resumeData.linkedin_url) fields.add("linkedin_url");
    if (resumeData.github_url) fields.add("github_url");
    if (resumeData.portfolio_url) fields.add("portfolio_url");
    if (resumeData.summary) fields.add("summary");

    return fields;
  }, [resumeData]);

  const {
    register,
    formState: { errors },
    control,
  } = useForm<PersonalInfoFormValues>({
    resolver: zodResolver(personalInfoSchema),
    defaultValues: {
      full_name: data.personalInfo.full_name,
      phone: data.personalInfo.phone,
      location: data.personalInfo.location,
      linkedin_url: data.personalInfo.linkedin_url,
      github_url: data.personalInfo.github_url,
      portfolio_url: data.personalInfo.portfolio_url,
      summary: data.personalInfo.summary,
    },
    mode: "onBlur",
  });

  // Watch all fields and sync to parent state
  const watchedValues = useWatch({ control });

  useEffect(() => {
    const currentInfo: PersonalInfoData = {
      full_name: watchedValues.full_name ?? "",
      phone: watchedValues.phone ?? "",
      location: watchedValues.location ?? "",
      linkedin_url: watchedValues.linkedin_url ?? "",
      github_url: watchedValues.github_url ?? "",
      portfolio_url: watchedValues.portfolio_url ?? "",
      summary: watchedValues.summary ?? "",
    };

    // Only update if values actually changed
    const prev = data.personalInfo;
    const changed =
      currentInfo.full_name !== prev.full_name ||
      currentInfo.phone !== prev.phone ||
      currentInfo.location !== prev.location ||
      currentInfo.linkedin_url !== prev.linkedin_url ||
      currentInfo.github_url !== prev.github_url ||
      currentInfo.portfolio_url !== prev.portfolio_url ||
      currentInfo.summary !== prev.summary;

    if (changed) {
      onUpdate({ personalInfo: currentInfo });
    }
  }, [watchedValues, data.personalInfo, onUpdate]);

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h2 className="text-xl font-bold text-foreground">
          Personal Information
        </h2>
        <p className="text-sm text-foreground/60">
          Tell us about yourself. This helps employers find and contact you.
        </p>
      </div>

      <div className="grid gap-5 sm:grid-cols-2">
        {/* Full Name */}
        <div className="sm:col-span-2">
          <FormField
            label="Full Name"
            htmlFor="full_name"
            error={errors.full_name?.message}
          >
            {autoFilledFields.has("full_name") && <AutoFilledBadge />}
            <Input
              id="full_name"
              placeholder="John Doe"
              {...register("full_name")}
              error={!!errors.full_name}
              className={cn(
                autoFilledFields.has("full_name") &&
                  "bg-blue-50/50 dark:bg-blue-950/10",
              )}
            />
          </FormField>
        </div>

        {/* Phone */}
        <FormField
          label="Phone Number"
          htmlFor="phone"
          error={errors.phone?.message}
        >
          {autoFilledFields.has("phone") && <AutoFilledBadge />}
          <Input
            id="phone"
            type="tel"
            placeholder="+1 (555) 000-0000"
            {...register("phone")}
            error={!!errors.phone}
            className={cn(
              autoFilledFields.has("phone") &&
                "bg-blue-50/50 dark:bg-blue-950/10",
            )}
          />
        </FormField>

        {/* Location */}
        <FormField
          label="Location"
          htmlFor="location"
          error={errors.location?.message}
        >
          {autoFilledFields.has("location") && <AutoFilledBadge />}
          <Input
            id="location"
            placeholder="San Francisco, CA"
            {...register("location")}
            error={!!errors.location}
            className={cn(
              autoFilledFields.has("location") &&
                "bg-blue-50/50 dark:bg-blue-950/10",
            )}
          />
        </FormField>

        {/* LinkedIn URL */}
        <FormField
          label="LinkedIn URL"
          htmlFor="linkedin_url"
          error={errors.linkedin_url?.message}
        >
          {autoFilledFields.has("linkedin_url") && <AutoFilledBadge />}
          <Input
            id="linkedin_url"
            type="url"
            placeholder="https://linkedin.com/in/johndoe"
            {...register("linkedin_url")}
            error={!!errors.linkedin_url}
            className={cn(
              autoFilledFields.has("linkedin_url") &&
                "bg-blue-50/50 dark:bg-blue-950/10",
            )}
          />
        </FormField>

        {/* GitHub URL */}
        <FormField
          label="GitHub URL"
          htmlFor="github_url"
          error={errors.github_url?.message}
        >
          {autoFilledFields.has("github_url") && <AutoFilledBadge />}
          <Input
            id="github_url"
            type="url"
            placeholder="https://github.com/johndoe"
            {...register("github_url")}
            error={!!errors.github_url}
            className={cn(
              autoFilledFields.has("github_url") &&
                "bg-blue-50/50 dark:bg-blue-950/10",
            )}
          />
        </FormField>

        {/* Portfolio URL */}
        <FormField
          label="Portfolio URL"
          htmlFor="portfolio_url"
          error={errors.portfolio_url?.message}
        >
          {autoFilledFields.has("portfolio_url") && <AutoFilledBadge />}
          <Input
            id="portfolio_url"
            type="url"
            placeholder="https://johndoe.dev"
            {...register("portfolio_url")}
            error={!!errors.portfolio_url}
            className={cn(
              autoFilledFields.has("portfolio_url") &&
                "bg-blue-50/50 dark:bg-blue-950/10",
            )}
          />
        </FormField>

        {/* Summary */}
        <div className="sm:col-span-2">
          <FormField
            label="Professional Summary"
            htmlFor="summary"
            error={errors.summary?.message}
          >
            {autoFilledFields.has("summary") && <AutoFilledBadge />}
            <Textarea
              id="summary"
              placeholder="A brief summary of your professional background, key skills, and career goals..."
              rows={4}
              {...register("summary")}
              error={!!errors.summary}
              className={cn(
                autoFilledFields.has("summary") &&
                  "bg-blue-50/50 dark:bg-blue-950/10",
              )}
            />
          </FormField>
        </div>
      </div>

      <p className="text-center text-sm text-foreground/50">
        Looking good! This information helps employers reach out to you.
      </p>
    </div>
  );
}
