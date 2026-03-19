"use client";

import * as Tabs from "@radix-ui/react-tabs";
import * as Progress from "@radix-ui/react-progress";
import { useProfile } from "@/hooks/useProfile";
import { PersonalInfoForm } from "./personal-info-form";
import { SkillsForm } from "./skills-form";
import { ExperienceForm } from "./experience-form";
import { EducationForm } from "./education-form";
import { PreferencesForm } from "./preferences-form";
import { ResumeManager } from "./resume-manager";
import { cn } from "@/lib/utils";

const TABS = [
  { value: "resumes", label: "Resumes" },
  { value: "personal", label: "Personal Info" },
  { value: "skills", label: "Skills" },
  { value: "experience", label: "Experience" },
  { value: "education", label: "Education" },
  { value: "preferences", label: "Preferences" },
] as const;

function ProfileSkeleton() {
  return (
    <div className="space-y-6" role="status">
      <div className="h-6 w-48 animate-pulse rounded bg-foreground/10" />
      <div className="h-3 w-full animate-pulse rounded-full bg-foreground/10" />
      <div className="h-10 w-full animate-pulse rounded-lg bg-foreground/10" />
      <div className="space-y-4">
        <div className="h-10 w-full animate-pulse rounded-lg bg-foreground/10" />
        <div className="h-10 w-full animate-pulse rounded-lg bg-foreground/10" />
        <div className="h-10 w-full animate-pulse rounded-lg bg-foreground/10" />
      </div>
      <span className="sr-only">Loading profile...</span>
    </div>
  );
}

export function ProfileContent() {
  const { profile, isLoading } = useProfile();

  if (isLoading) {
    return <ProfileSkeleton />;
  }

  const completeness = profile?.profile_completeness ?? 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Your Profile</h1>
        <p className="mt-1 text-foreground/60">
          Keep your profile up to date to get the best job matches.
        </p>
      </div>

      <div className="flex items-center gap-4 rounded-lg border border-foreground/10 px-4 py-3">
        <span className="shrink-0 text-sm font-medium text-foreground/70">
          Profile: {completeness}%
        </span>
        <Progress.Root
          className="h-2 flex-1 overflow-hidden rounded-full bg-foreground/10"
          value={completeness}
          aria-label={`Profile ${completeness}% complete`}
        >
          <Progress.Indicator
            className={cn(
              "h-full rounded-full transition-all duration-500",
              completeness >= 80
                ? "bg-green-500"
                : completeness >= 50
                  ? "bg-yellow-500"
                  : "bg-red-500",
            )}
            style={{ width: `${completeness}%` }}
          />
        </Progress.Root>
      </div>

      <Tabs.Root defaultValue="resumes">
        <Tabs.List
          className="flex gap-1 overflow-x-auto border-b border-foreground/10 pb-px"
          aria-label="Profile sections"
        >
          {TABS.map((tab) => (
            <Tabs.Trigger
              key={tab.value}
              value={tab.value}
              className={cn(
                "shrink-0 whitespace-nowrap border-b-2 px-4 py-2.5 text-sm font-medium transition-colors",
                "border-transparent text-foreground/60 hover:text-foreground",
                "data-[state=active]:border-blue-600 data-[state=active]:text-blue-600",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2",
              )}
            >
              {tab.label}
            </Tabs.Trigger>
          ))}
        </Tabs.List>

        <div className="pt-6">
          <Tabs.Content value="resumes">
            <ResumeManager />
          </Tabs.Content>
          <Tabs.Content value="personal">
            <PersonalInfoForm />
          </Tabs.Content>
          <Tabs.Content value="skills">
            <SkillsForm />
          </Tabs.Content>
          <Tabs.Content value="experience">
            <ExperienceForm />
          </Tabs.Content>
          <Tabs.Content value="education">
            <EducationForm />
          </Tabs.Content>
          <Tabs.Content value="preferences">
            <PreferencesForm />
          </Tabs.Content>
        </div>
      </Tabs.Root>
    </div>
  );
}
