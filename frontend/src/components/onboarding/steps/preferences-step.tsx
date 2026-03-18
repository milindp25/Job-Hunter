"use client";

import { useCallback } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { TagInput } from "@/components/ui/tag-input";
import { cn } from "@/lib/utils";
import type { OnboardingStepProps } from "../onboarding-types";

const JOB_TYPES = [
  { value: "full-time", label: "Full-time" },
  { value: "part-time", label: "Part-time" },
  { value: "contract", label: "Contract" },
  { value: "internship", label: "Internship" },
] as const;

export function PreferencesStep({ data, onUpdate }: OnboardingStepProps) {
  const preferences = data.preferences;

  const updatePreferences = useCallback(
    (updates: Partial<typeof preferences>) => {
      onUpdate({
        preferences: { ...preferences, ...updates },
      });
    },
    [preferences, onUpdate],
  );

  const toggleJobType = useCallback(
    (jobType: string) => {
      const current = preferences.job_types;
      const updated = current.includes(jobType)
        ? current.filter((t) => t !== jobType)
        : [...current, jobType];
      updatePreferences({ job_types: updated });
    },
    [preferences.job_types, updatePreferences],
  );

  const handleSalaryChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const raw = e.target.value.replace(/[^0-9]/g, "");
      const num = raw ? parseInt(raw, 10) : null;
      updatePreferences({ min_salary: num });
    },
    [updatePreferences],
  );

  const formatSalary = (value: number | null): string => {
    if (value === null || value === 0) return "";
    return value.toLocaleString("en-US");
  };

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h2 className="text-xl font-bold text-foreground">Job Preferences</h2>
        <p className="text-sm text-foreground/60">
          Tell us what you&apos;re looking for so we can find the best matches
          for you.
        </p>
      </div>

      {/* Desired Roles */}
      <div className="space-y-2">
        <Label htmlFor="desired-roles">Desired Roles</Label>
        <p className="text-xs text-foreground/50">
          Type a role and press Enter to add it.
        </p>
        <TagInput
          id="desired-roles"
          value={preferences.desired_roles}
          onChange={(roles) => updatePreferences({ desired_roles: roles })}
          placeholder="e.g. Frontend Engineer, Product Manager..."
        />
      </div>

      {/* Desired Locations */}
      <div className="space-y-2">
        <Label htmlFor="desired-locations">Desired Locations</Label>
        <p className="text-xs text-foreground/50">
          Add locations where you&apos;d like to work. Type &quot;Remote&quot;
          if you prefer remote work.
        </p>
        <TagInput
          id="desired-locations"
          value={preferences.desired_locations}
          onChange={(locations) =>
            updatePreferences({ desired_locations: locations })
          }
          placeholder="e.g. San Francisco, New York, Remote..."
        />
        {!preferences.desired_locations.includes("Remote") && (
          <button
            type="button"
            onClick={() =>
              updatePreferences({
                desired_locations: [
                  ...preferences.desired_locations,
                  "Remote",
                ],
              })
            }
            className="text-xs text-blue-600 hover:underline"
          >
            + Add &quot;Remote&quot; as an option
          </button>
        )}
      </div>

      {/* Minimum Salary */}
      <div className="space-y-2">
        <Label htmlFor="min-salary">Minimum Salary (USD / year)</Label>
        <div className="relative">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-foreground/50">
            $
          </span>
          <Input
            id="min-salary"
            type="text"
            inputMode="numeric"
            placeholder="80,000"
            value={formatSalary(preferences.min_salary)}
            onChange={handleSalaryChange}
            className="pl-7"
          />
        </div>
      </div>

      {/* Job Type */}
      <fieldset className="space-y-3">
        <legend className="text-sm font-medium text-foreground">
          Job Type
        </legend>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {JOB_TYPES.map((type) => {
            const isSelected = preferences.job_types.includes(type.value);
            return (
              <button
                key={type.value}
                type="button"
                onClick={() => toggleJobType(type.value)}
                aria-pressed={isSelected}
                className={cn(
                  "flex items-center justify-center rounded-lg border px-4 py-2.5 text-sm font-medium transition-colors",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2",
                  isSelected
                    ? "border-blue-600 bg-blue-50 text-blue-700 dark:bg-blue-950/30 dark:text-blue-300"
                    : "border-foreground/15 text-foreground/70 hover:border-foreground/30 hover:bg-foreground/5",
                )}
              >
                {type.label}
              </button>
            );
          })}
        </div>
      </fieldset>

      <p className="text-center text-sm text-foreground/50">
        Almost there! Your preferences help us find the best job matches.
      </p>
    </div>
  );
}
