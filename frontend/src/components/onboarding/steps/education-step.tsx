"use client";

import { useCallback } from "react";
import { Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { TagInput } from "@/components/ui/tag-input";
import type { Education } from "@/lib/types";
import type { OnboardingStepProps } from "../onboarding-types";

function createEmptyEducation(): Education {
  return {
    institution: "",
    degree: "",
    field: "",
    start_date: "",
    end_date: null,
  };
}

/** Format a date string to YYYY-MM for month input */
function toMonthValue(date: string | null): string {
  if (!date) return "";
  if (/^\d{4}-\d{2}$/.test(date)) return date;
  if (date.length >= 7) return date.substring(0, 7);
  return date;
}

export function EducationStep({
  data,
  onUpdate,
  resumeData,
}: OnboardingStepProps) {
  const educationEntries = data.education.education;
  const certifications = data.education.certifications;

  const updateEducation = useCallback(
    (updated: Education[]) => {
      onUpdate({
        education: { education: updated, certifications },
      });
    },
    [onUpdate, certifications],
  );

  const updateCertifications = useCallback(
    (updated: string[]) => {
      onUpdate({
        education: { education: educationEntries, certifications: updated },
      });
    },
    [onUpdate, educationEntries],
  );

  const addEducation = useCallback(() => {
    updateEducation([...educationEntries, createEmptyEducation()]);
  }, [educationEntries, updateEducation]);

  const removeEducation = useCallback(
    (index: number) => {
      updateEducation(educationEntries.filter((_, i) => i !== index));
    },
    [educationEntries, updateEducation],
  );

  const updateEntry = useCallback(
    (index: number, field: keyof Education, value: string | null) => {
      const updated = educationEntries.map((edu, i) =>
        i === index ? { ...edu, [field]: value } : edu,
      );
      updateEducation(updated);
    },
    [educationEntries, updateEducation],
  );

  const isAutoFilled =
    resumeData?.education && resumeData.education.length > 0;

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h2 className="text-xl font-bold text-foreground">
          Education &amp; Certifications
        </h2>
        <p className="text-sm text-foreground/60">
          Add your educational background and any professional certifications.
        </p>
        {isAutoFilled && (
          <p className="text-xs text-blue-600 dark:text-blue-400">
            Education has been pre-filled from your resume. Feel free to edit or
            add more.
          </p>
        )}
      </div>

      {/* Education entries */}
      <div className="space-y-6">
        <h3 className="text-base font-semibold text-foreground">Education</h3>

        {educationEntries.map((edu, index) => (
          <div
            key={index}
            className="space-y-4 rounded-lg border border-foreground/10 p-4"
          >
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-foreground/70">
                Education {index + 1}
              </span>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => removeEducation(index)}
                aria-label={`Remove education: ${edu.institution || `entry ${index + 1}`}`}
                className="text-red-500 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/20"
              >
                <Trash2 className="h-4 w-4" />
                Remove
              </Button>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              {/* Institution */}
              <div className="sm:col-span-2 space-y-1.5">
                <Label htmlFor={`edu-institution-${index}`}>Institution</Label>
                <Input
                  id={`edu-institution-${index}`}
                  placeholder="University name"
                  value={edu.institution}
                  onChange={(e) =>
                    updateEntry(index, "institution", e.target.value)
                  }
                />
              </div>

              {/* Degree */}
              <div className="space-y-1.5">
                <Label htmlFor={`edu-degree-${index}`}>Degree</Label>
                <Input
                  id={`edu-degree-${index}`}
                  placeholder="Bachelor's, Master's, PhD..."
                  value={edu.degree}
                  onChange={(e) =>
                    updateEntry(index, "degree", e.target.value)
                  }
                />
              </div>

              {/* Field of Study */}
              <div className="space-y-1.5">
                <Label htmlFor={`edu-field-${index}`}>Field of Study</Label>
                <Input
                  id={`edu-field-${index}`}
                  placeholder="Computer Science"
                  value={edu.field}
                  onChange={(e) =>
                    updateEntry(index, "field", e.target.value)
                  }
                />
              </div>

              {/* Start Date */}
              <div className="space-y-1.5">
                <Label htmlFor={`edu-start-${index}`}>Start Date</Label>
                <Input
                  id={`edu-start-${index}`}
                  type="month"
                  value={toMonthValue(edu.start_date)}
                  onChange={(e) =>
                    updateEntry(index, "start_date", e.target.value)
                  }
                />
              </div>

              {/* End Date */}
              <div className="space-y-1.5">
                <Label htmlFor={`edu-end-${index}`}>End Date</Label>
                <Input
                  id={`edu-end-${index}`}
                  type="month"
                  value={toMonthValue(edu.end_date)}
                  onChange={(e) =>
                    updateEntry(
                      index,
                      "end_date",
                      e.target.value || null,
                    )
                  }
                />
              </div>
            </div>
          </div>
        ))}

        <Button
          type="button"
          variant="outline"
          onClick={addEducation}
          className="w-full"
        >
          <Plus className="h-4 w-4" />
          Add Education
        </Button>
      </div>

      {/* Certifications */}
      <div className="space-y-3">
        <h3 className="text-base font-semibold text-foreground">
          Certifications
        </h3>
        <p className="text-xs text-foreground/50">
          Type a certification name and press Enter to add it.
        </p>
        <TagInput
          id="certifications"
          value={certifications}
          onChange={updateCertifications}
          placeholder="e.g. AWS Solutions Architect, PMP..."
        />
      </div>

      <p className="text-center text-sm text-foreground/50">
        Keep going! Education and certifications add credibility to your
        profile.
      </p>
    </div>
  );
}
