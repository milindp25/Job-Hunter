"use client";

import { useCallback } from "react";
import { Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import type { Experience } from "@/lib/types";
import type { OnboardingStepProps } from "../onboarding-types";

function createEmptyExperience(): Experience {
  return {
    company: "",
    title: "",
    description: "",
    start_date: "",
    end_date: null,
  };
}

/** Format a date string (YYYY-MM or ISO) to YYYY-MM for month input */
function toMonthValue(date: string | null): string {
  if (!date) return "";
  // Already YYYY-MM
  if (/^\d{4}-\d{2}$/.test(date)) return date;
  // ISO date: take first 7 chars
  if (date.length >= 7) return date.substring(0, 7);
  return date;
}

export function ExperienceStep({
  data,
  onUpdate,
  resumeData,
}: OnboardingStepProps) {
  const experiences = data.experience.experience;

  const updateExperiences = useCallback(
    (updated: Experience[]) => {
      onUpdate({ experience: { experience: updated } });
    },
    [onUpdate],
  );

  const addExperience = useCallback(() => {
    updateExperiences([...experiences, createEmptyExperience()]);
  }, [experiences, updateExperiences]);

  const removeExperience = useCallback(
    (index: number) => {
      updateExperiences(experiences.filter((_, i) => i !== index));
    },
    [experiences, updateExperiences],
  );

  const updateEntry = useCallback(
    (index: number, field: keyof Experience, value: string | null) => {
      const updated = experiences.map((exp, i) =>
        i === index ? { ...exp, [field]: value } : exp,
      );
      updateExperiences(updated);
    },
    [experiences, updateExperiences],
  );

  const togglePresent = useCallback(
    (index: number) => {
      const exp = experiences[index];
      const updated = experiences.map((e, i) =>
        i === index
          ? { ...e, end_date: exp.end_date === null ? "" : null }
          : e,
      );
      updateExperiences(updated);
    },
    [experiences, updateExperiences],
  );

  const isAutoFilled =
    resumeData?.experience && resumeData.experience.length > 0;

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h2 className="text-xl font-bold text-foreground">Work Experience</h2>
        <p className="text-sm text-foreground/60">
          Share your professional experience. This gives employers a clear
          picture of your background.
        </p>
        {isAutoFilled && (
          <p className="text-xs text-blue-600 dark:text-blue-400">
            Experience has been pre-filled from your resume. Feel free to edit or
            add more.
          </p>
        )}
      </div>

      {/* Experience entries */}
      <div className="space-y-6">
        {experiences.map((exp, index) => (
          <div
            key={index}
            className="space-y-4 rounded-lg border border-foreground/10 p-4"
          >
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-foreground/70">
                Position {index + 1}
              </span>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => removeExperience(index)}
                aria-label={`Remove experience: ${exp.title || `position ${index + 1}`}`}
                className="text-red-500 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/20"
              >
                <Trash2 className="h-4 w-4" />
                Remove
              </Button>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              {/* Company */}
              <div className="space-y-1.5">
                <Label htmlFor={`exp-company-${index}`}>Company</Label>
                <Input
                  id={`exp-company-${index}`}
                  placeholder="Company name"
                  value={exp.company}
                  onChange={(e) =>
                    updateEntry(index, "company", e.target.value)
                  }
                />
              </div>

              {/* Title */}
              <div className="space-y-1.5">
                <Label htmlFor={`exp-title-${index}`}>Job Title</Label>
                <Input
                  id={`exp-title-${index}`}
                  placeholder="Software Engineer"
                  value={exp.title}
                  onChange={(e) => updateEntry(index, "title", e.target.value)}
                />
              </div>

              {/* Start Date */}
              <div className="space-y-1.5">
                <Label htmlFor={`exp-start-${index}`}>Start Date</Label>
                <Input
                  id={`exp-start-${index}`}
                  type="month"
                  value={toMonthValue(exp.start_date)}
                  onChange={(e) =>
                    updateEntry(index, "start_date", e.target.value)
                  }
                />
              </div>

              {/* End Date */}
              <div className="space-y-1.5">
                <Label htmlFor={`exp-end-${index}`}>End Date</Label>
                <div className="space-y-2">
                  <Input
                    id={`exp-end-${index}`}
                    type="month"
                    value={toMonthValue(exp.end_date)}
                    onChange={(e) =>
                      updateEntry(index, "end_date", e.target.value || null)
                    }
                    disabled={exp.end_date === null}
                  />
                  <label className="flex items-center gap-2 text-sm text-foreground/70">
                    <input
                      type="checkbox"
                      checked={exp.end_date === null}
                      onChange={() => togglePresent(index)}
                      className="rounded border-foreground/20 text-blue-600 focus:ring-blue-500"
                    />
                    I currently work here
                  </label>
                </div>
              </div>

              {/* Description */}
              <div className="sm:col-span-2 space-y-1.5">
                <Label htmlFor={`exp-desc-${index}`}>Description</Label>
                <Textarea
                  id={`exp-desc-${index}`}
                  placeholder="Describe your role, responsibilities, and key achievements..."
                  rows={3}
                  value={exp.description}
                  onChange={(e) =>
                    updateEntry(index, "description", e.target.value)
                  }
                />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Add experience button */}
      <Button
        type="button"
        variant="outline"
        onClick={addExperience}
        className="w-full"
      >
        <Plus className="h-4 w-4" />
        Add Experience
      </Button>

      {experiences.length === 0 && (
        <p className="text-center text-sm text-foreground/50">
          No experience added yet. Add your work history or skip this step.
        </p>
      )}

      <p className="text-center text-sm text-foreground/50">
        You&apos;re making great progress! Experience details help employers
        understand your journey.
      </p>
    </div>
  );
}
