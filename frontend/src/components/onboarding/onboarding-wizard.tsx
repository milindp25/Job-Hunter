"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ChevronLeft, ChevronRight, SkipForward } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { StepProgress } from "./step-progress";
import { WelcomeStep } from "./steps/welcome-step";
import { PersonalInfoStep } from "./steps/personal-info-step";
import { SkillsStep } from "./steps/skills-step";
import { ExperienceStep } from "./steps/experience-step";
import { EducationStep } from "./steps/education-step";
import { PreferencesStep } from "./steps/preferences-step";
import { ReviewStep } from "./steps/review-step";
import { TOTAL_STEPS } from "./onboarding-types";
import type { OnboardingData } from "./onboarding-types";

const INITIAL_DATA: OnboardingData = {
  resumeData: null,
  personalInfo: {
    full_name: "",
    phone: "",
    location: "",
    linkedin_url: "",
    github_url: "",
    portfolio_url: "",
    summary: "",
  },
  skills: { skills: [] },
  experience: { experience: [] },
  education: { education: [], certifications: [] },
  preferences: {
    desired_roles: [],
    desired_locations: [],
    min_salary: null,
    job_types: [],
  },
  linkedinUrl: "",
};

export function OnboardingWizard({ userName }: { userName?: string }) {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(
    new Set(),
  );
  const [data, setData] = useState<OnboardingData>(() => ({
    ...INITIAL_DATA,
    personalInfo: {
      ...INITIAL_DATA.personalInfo,
      full_name: userName ?? "",
    },
  }));
  const [isSaving, setIsSaving] = useState(false);
  const [isCompleting, setIsCompleting] = useState(false);
  const stepContentRef = useRef<HTMLDivElement>(null);

  // Focus management on step change
  useEffect(() => {
    if (stepContentRef.current) {
      stepContentRef.current.focus();
    }
  }, [currentStep]);

  const updateData = useCallback((updates: Partial<OnboardingData>) => {
    setData((prev) => ({ ...prev, ...updates }));
  }, []);

  const saveStepData = useCallback(async () => {
    setIsSaving(true);
    try {
      await api.put("/users/me/onboarding", {
        step: currentStep,
        personal_info: {
          phone: data.personalInfo.phone || null,
          location: data.personalInfo.location || null,
          linkedin_url: data.personalInfo.linkedin_url || null,
          github_url: data.personalInfo.github_url || null,
          portfolio_url: data.personalInfo.portfolio_url || null,
          summary: data.personalInfo.summary || null,
        },
        skills: data.skills.skills.filter((s) => s.name.trim() !== ""),
        experience: data.experience.experience.filter(
          (e) => e.company.trim() !== "" || e.title.trim() !== "",
        ),
        education: data.education.education.filter(
          (e) => e.institution.trim() !== "",
        ),
        certifications: data.education.certifications,
        preferences: {
          desired_roles: data.preferences.desired_roles,
          desired_locations: data.preferences.desired_locations,
          min_salary: data.preferences.min_salary,
          job_types: data.preferences.job_types,
        },
        linkedin_url: data.linkedinUrl || null,
      });
    } catch {
      // Save silently fails -- data persists in local state
      // The user can still proceed and we'll try again on next transition
    } finally {
      setIsSaving(false);
    }
  }, [currentStep, data]);

  const goToStep = useCallback(
    async (step: number) => {
      if (step < 1 || step > TOTAL_STEPS) return;

      // Auto-save on step transition
      await saveStepData();

      // Mark current step as completed when moving forward
      if (step > currentStep) {
        setCompletedSteps((prev) => new Set([...prev, currentStep]));
      }

      setCurrentStep(step);
    },
    [currentStep, saveStepData],
  );

  const handleNext = useCallback(() => {
    if (currentStep < TOTAL_STEPS) {
      goToStep(currentStep + 1);
    }
  }, [currentStep, goToStep]);

  const handleBack = useCallback(() => {
    if (currentStep > 1) {
      goToStep(currentStep - 1);
    }
  }, [currentStep, goToStep]);

  const handleSkip = useCallback(() => {
    handleNext();
  }, [handleNext]);

  const handleComplete = useCallback(async () => {
    setIsCompleting(true);
    try {
      // Save final data first
      await saveStepData();

      // Mark all steps as completed
      setCompletedSteps(
        new Set(Array.from({ length: TOTAL_STEPS }, (_, i) => i + 1)),
      );

      // Complete onboarding
      await api.post("/users/me/onboarding/complete");

      toast.success(
        "Profile complete! Welcome to Job Hunter. Let's find your next opportunity.",
      );

      router.push("/dashboard");
    } catch {
      toast.error(
        "Something went wrong completing your profile. Please try again.",
      );
    } finally {
      setIsCompleting(false);
    }
  }, [saveStepData, router]);

  const handleStepClick = useCallback(
    (step: number) => {
      if (completedSteps.has(step) || step === currentStep) {
        goToStep(step);
      }
    },
    [completedSteps, currentStep, goToStep],
  );

  const isLastStep = currentStep === TOTAL_STEPS;
  const isFirstStep = currentStep === 1;

  const stepProps = {
    data,
    onUpdate: updateData,
    resumeData: data.resumeData,
  };

  return (
    <div className="mx-auto w-full max-w-3xl space-y-8">
      {/* Progress bar */}
      <StepProgress
        currentStep={currentStep}
        completedSteps={completedSteps}
        onStepClick={handleStepClick}
      />

      {/* Step content */}
      <div
        ref={stepContentRef}
        tabIndex={-1}
        className="rounded-xl border border-foreground/10 bg-background p-6 shadow-sm focus:outline-none sm:p-8"
        aria-live="polite"
      >
        {currentStep === 1 && <WelcomeStep {...stepProps} />}
        {currentStep === 2 && <PersonalInfoStep {...stepProps} />}
        {currentStep === 3 && <SkillsStep {...stepProps} />}
        {currentStep === 4 && <ExperienceStep {...stepProps} />}
        {currentStep === 5 && <EducationStep {...stepProps} />}
        {currentStep === 6 && <PreferencesStep {...stepProps} />}
        {currentStep === 7 && (
          <ReviewStep data={data} onEditStep={handleStepClick} />
        )}
      </div>

      {/* Navigation buttons */}
      <div className="flex items-center justify-between">
        {/* Left side: Back button */}
        <div>
          {!isFirstStep && (
            <Button
              variant="ghost"
              onClick={handleBack}
              disabled={isSaving}
            >
              <ChevronLeft className="h-4 w-4" />
              Back
            </Button>
          )}
        </div>

        {/* Right side: Skip + Next/Complete */}
        <div className="flex items-center gap-3">
          {/* Saving indicator */}
          {isSaving && (
            <span className="text-xs text-foreground/40 animate-pulse">
              Saving...
            </span>
          )}

          {/* Skip button (not shown on Review step) */}
          {!isLastStep && (
            <Button
              variant="ghost"
              onClick={handleSkip}
              disabled={isSaving}
              className="text-foreground/50"
            >
              Skip
              <SkipForward className="h-4 w-4" />
            </Button>
          )}

          {/* Next or Complete */}
          {isLastStep ? (
            <Button
              onClick={handleComplete}
              loading={isCompleting}
              disabled={isSaving}
              size="lg"
              className={cn(
                "bg-green-600 hover:bg-green-700 text-white",
              )}
            >
              Complete Profile
            </Button>
          ) : (
            <Button
              onClick={handleNext}
              disabled={isSaving}
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
