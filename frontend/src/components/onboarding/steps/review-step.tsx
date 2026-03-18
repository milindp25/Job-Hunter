"use client";

import {
  User,
  Wrench,
  Briefcase,
  GraduationCap,
  Target,
  Edit3,
  AlertCircle,
} from "lucide-react";
import * as Progress from "@radix-ui/react-progress";
import { cn } from "@/lib/utils";
import type { OnboardingData } from "../onboarding-types";

interface ReviewStepProps {
  data: OnboardingData;
  onEditStep: (step: number) => void;
}

function calculateCompleteness(data: OnboardingData): {
  percentage: number;
  missing: string[];
} {
  const missing: string[] = [];
  let filled = 0;
  const total = 10;

  // Personal info
  if (data.personalInfo.full_name) filled++;
  else missing.push("Full name");

  if (data.personalInfo.phone) filled++;
  else missing.push("Phone number");

  if (data.personalInfo.location) filled++;
  else missing.push("Location");

  if (data.personalInfo.summary) filled++;
  else missing.push("Professional summary");

  // Skills
  if (data.skills.skills.length > 0) filled++;
  else missing.push("Skills");

  // Experience
  if (data.experience.experience.length > 0) filled++;
  else missing.push("Work experience");

  // Education
  if (data.education.education.length > 0) filled++;
  else missing.push("Education");

  // Preferences
  if (data.preferences.desired_roles.length > 0) filled++;
  else missing.push("Desired roles");

  if (data.preferences.desired_locations.length > 0) filled++;
  else missing.push("Desired locations");

  if (data.preferences.job_types.length > 0) filled++;
  else missing.push("Job type");

  return {
    percentage: Math.round((filled / total) * 100),
    missing,
  };
}

function SectionHeader({
  icon: Icon,
  title,
  step,
  onEdit,
}: {
  icon: React.ElementType;
  title: string;
  step: number;
  onEdit: (step: number) => void;
}) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <Icon className="h-4 w-4 text-foreground/50" />
        <h3 className="text-sm font-semibold text-foreground">{title}</h3>
      </div>
      <button
        type="button"
        onClick={() => onEdit(step)}
        className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 rounded"
        aria-label={`Edit ${title}`}
      >
        <Edit3 className="h-3 w-3" />
        Edit
      </button>
    </div>
  );
}

function DataRow({
  label,
  value,
  empty = "Not provided",
}: {
  label: string;
  value: string | null | undefined;
  empty?: string;
}) {
  return (
    <div className="flex items-baseline justify-between gap-4 text-sm">
      <span className="text-foreground/50 shrink-0">{label}</span>
      <span
        className={cn(
          "text-right truncate",
          value ? "text-foreground" : "text-foreground/30 italic",
        )}
      >
        {value || empty}
      </span>
    </div>
  );
}

function TagList({
  items,
  empty = "None added",
}: {
  items: string[];
  empty?: string;
}) {
  if (items.length === 0) {
    return <span className="text-sm text-foreground/30 italic">{empty}</span>;
  }
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((item, i) => (
        <span
          key={`${item}-${i}`}
          className="inline-flex rounded-md bg-foreground/5 px-2 py-0.5 text-xs text-foreground/70"
        >
          {item}
        </span>
      ))}
    </div>
  );
}

export function ReviewStep({ data, onEditStep }: ReviewStepProps) {
  const { percentage, missing } = calculateCompleteness(data);

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h2 className="text-xl font-bold text-foreground">
          Review Your Profile
        </h2>
        <p className="text-sm text-foreground/60">
          Review the information below and complete your profile. You can always
          update it later.
        </p>
      </div>

      {/* Completeness */}
      <div className="rounded-lg border border-foreground/10 p-4 space-y-3">
        <div className="flex items-center justify-between text-sm">
          <span className="font-medium text-foreground">
            Profile Completeness
          </span>
          <span
            className={cn(
              "font-semibold",
              percentage >= 80
                ? "text-green-600"
                : percentage >= 50
                  ? "text-amber-600"
                  : "text-red-500",
            )}
          >
            {percentage}%
          </span>
        </div>
        <Progress.Root
          className="h-3 w-full overflow-hidden rounded-full bg-foreground/10"
          value={percentage}
        >
          <Progress.Indicator
            className={cn(
              "h-full rounded-full transition-all duration-500",
              percentage >= 80
                ? "bg-green-500"
                : percentage >= 50
                  ? "bg-amber-500"
                  : "bg-red-500",
            )}
            style={{ width: `${percentage}%` }}
          />
        </Progress.Root>

        {missing.length > 0 && (
          <div className="flex items-start gap-2 text-xs text-amber-600 dark:text-amber-400">
            <AlertCircle className="h-3.5 w-3.5 shrink-0 mt-0.5" />
            <span>
              Missing: {missing.join(", ")}. Complete these for better job
              matches.
            </span>
          </div>
        )}
      </div>

      {/* Personal Info Section */}
      <div className="space-y-3 rounded-lg border border-foreground/10 p-4">
        <SectionHeader
          icon={User}
          title="Personal Information"
          step={2}
          onEdit={onEditStep}
        />
        <div className="space-y-2">
          <DataRow label="Name" value={data.personalInfo.full_name} />
          <DataRow label="Phone" value={data.personalInfo.phone} />
          <DataRow label="Location" value={data.personalInfo.location} />
          <DataRow label="LinkedIn" value={data.personalInfo.linkedin_url} />
          <DataRow label="GitHub" value={data.personalInfo.github_url} />
          <DataRow label="Portfolio" value={data.personalInfo.portfolio_url} />
          {data.personalInfo.summary && (
            <div className="pt-1">
              <span className="text-xs text-foreground/50">Summary</span>
              <p className="text-sm text-foreground mt-0.5 line-clamp-3">
                {data.personalInfo.summary}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Skills Section */}
      <div className="space-y-3 rounded-lg border border-foreground/10 p-4">
        <SectionHeader
          icon={Wrench}
          title="Skills"
          step={3}
          onEdit={onEditStep}
        />
        {data.skills.skills.length > 0 ? (
          <div className="space-y-1.5">
            {data.skills.skills.map((skill, i) => (
              <div
                key={`${skill.name}-${i}`}
                className="flex items-center justify-between text-sm"
              >
                <span className="text-foreground">{skill.name || "Unnamed"}</span>
                <span className="text-foreground/50 text-xs">
                  {skill.level} &middot; {skill.years}y
                </span>
              </div>
            ))}
          </div>
        ) : (
          <span className="text-sm text-foreground/30 italic">
            No skills added
          </span>
        )}
      </div>

      {/* Experience Section */}
      <div className="space-y-3 rounded-lg border border-foreground/10 p-4">
        <SectionHeader
          icon={Briefcase}
          title="Work Experience"
          step={4}
          onEdit={onEditStep}
        />
        {data.experience.experience.length > 0 ? (
          <div className="space-y-3">
            {data.experience.experience.map((exp, i) => (
              <div key={i} className="text-sm">
                <p className="font-medium text-foreground">
                  {exp.title || "Untitled"}{" "}
                  {exp.company && (
                    <span className="font-normal text-foreground/50">
                      at {exp.company}
                    </span>
                  )}
                </p>
                <p className="text-xs text-foreground/40">
                  {exp.start_date || "?"} &ndash;{" "}
                  {exp.end_date === null ? "Present" : exp.end_date || "?"}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <span className="text-sm text-foreground/30 italic">
            No experience added
          </span>
        )}
      </div>

      {/* Education Section */}
      <div className="space-y-3 rounded-lg border border-foreground/10 p-4">
        <SectionHeader
          icon={GraduationCap}
          title="Education & Certifications"
          step={5}
          onEdit={onEditStep}
        />
        {data.education.education.length > 0 ? (
          <div className="space-y-2">
            {data.education.education.map((edu, i) => (
              <div key={i} className="text-sm">
                <p className="font-medium text-foreground">
                  {edu.degree || "Degree"} in {edu.field || "Field"}
                </p>
                <p className="text-xs text-foreground/50">
                  {edu.institution || "Institution"}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <span className="text-sm text-foreground/30 italic">
            No education added
          </span>
        )}
        {data.education.certifications.length > 0 && (
          <div className="pt-2">
            <span className="text-xs text-foreground/50 block mb-1">
              Certifications
            </span>
            <TagList items={data.education.certifications} />
          </div>
        )}
      </div>

      {/* Preferences Section */}
      <div className="space-y-3 rounded-lg border border-foreground/10 p-4">
        <SectionHeader
          icon={Target}
          title="Job Preferences"
          step={6}
          onEdit={onEditStep}
        />
        <div className="space-y-3">
          <div>
            <span className="text-xs text-foreground/50">Desired Roles</span>
            <TagList items={data.preferences.desired_roles} />
          </div>
          <div>
            <span className="text-xs text-foreground/50">Locations</span>
            <TagList items={data.preferences.desired_locations} />
          </div>
          <DataRow
            label="Min. Salary"
            value={
              data.preferences.min_salary
                ? `$${data.preferences.min_salary.toLocaleString("en-US")}/yr`
                : null
            }
          />
          <div>
            <span className="text-xs text-foreground/50">Job Types</span>
            <TagList items={data.preferences.job_types} />
          </div>
        </div>
      </div>

      <p className="text-center text-sm text-foreground/50">
        {percentage >= 80
          ? "Your profile is looking great! Click Complete Profile to finish."
          : "Consider filling in the missing sections for better job matches."}
      </p>
    </div>
  );
}
