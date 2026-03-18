"use client";

import { Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { STEP_NAMES, TOTAL_STEPS } from "./onboarding-types";

interface StepProgressProps {
  currentStep: number;
  completedSteps: Set<number>;
  onStepClick: (step: number) => void;
}

export function StepProgress({
  currentStep,
  completedSteps,
  onStepClick,
}: StepProgressProps) {
  return (
    <nav aria-label="Onboarding progress" className="w-full">
      {/* Desktop: horizontal step bar */}
      <ol className="hidden sm:flex items-center justify-between">
        {STEP_NAMES.map((name, index) => {
          const stepNumber = index + 1;
          const isCompleted = completedSteps.has(stepNumber);
          const isCurrent = stepNumber === currentStep;
          const isClickable = isCompleted || isCurrent;

          return (
            <li
              key={name}
              className="flex flex-1 flex-col items-center relative"
            >
              {/* Connector line */}
              {index > 0 && (
                <div
                  className={cn(
                    "absolute top-4 right-1/2 w-full h-0.5 -translate-y-1/2",
                    completedSteps.has(stepNumber) || completedSteps.has(index)
                      ? "bg-blue-600"
                      : "bg-foreground/15",
                  )}
                  aria-hidden="true"
                />
              )}

              {/* Step circle */}
              <button
                type="button"
                onClick={() => isClickable && onStepClick(stepNumber)}
                disabled={!isClickable}
                aria-current={isCurrent ? "step" : undefined}
                aria-label={`Step ${stepNumber}: ${name}${isCompleted ? " (completed)" : isCurrent ? " (current)" : ""}`}
                className={cn(
                  "relative z-10 flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium transition-all",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2",
                  isCompleted
                    ? "bg-blue-600 text-white cursor-pointer hover:bg-blue-700"
                    : isCurrent
                      ? "bg-blue-600 text-white ring-2 ring-blue-300 ring-offset-2"
                      : "bg-foreground/10 text-foreground/40 cursor-default",
                )}
              >
                {isCompleted ? (
                  <Check className="h-4 w-4" aria-hidden="true" />
                ) : (
                  stepNumber
                )}
              </button>

              {/* Step name */}
              <span
                className={cn(
                  "mt-2 text-xs font-medium",
                  isCurrent
                    ? "text-blue-600"
                    : isCompleted
                      ? "text-foreground/70"
                      : "text-foreground/40",
                )}
              >
                {name}
              </span>
            </li>
          );
        })}
      </ol>

      {/* Mobile: simplified progress bar */}
      <div className="sm:hidden space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="font-medium text-foreground">
            Step {currentStep} of {TOTAL_STEPS}
          </span>
          <span className="text-foreground/60">
            {STEP_NAMES[currentStep - 1]}
          </span>
        </div>
        <div className="h-2 w-full overflow-hidden rounded-full bg-foreground/10">
          <div
            className="h-full rounded-full bg-blue-600 transition-all duration-300"
            style={{ width: `${(currentStep / TOTAL_STEPS) * 100}%` }}
            role="progressbar"
            aria-valuenow={currentStep}
            aria-valuemin={1}
            aria-valuemax={TOTAL_STEPS}
            aria-label={`Step ${currentStep} of ${TOTAL_STEPS}: ${STEP_NAMES[currentStep - 1]}`}
          />
        </div>

        {/* Mobile step dots */}
        <div className="flex justify-center gap-1.5 pt-1">
          {STEP_NAMES.map((name, index) => {
            const stepNumber = index + 1;
            const isCompleted = completedSteps.has(stepNumber);
            const isCurrent = stepNumber === currentStep;
            const isClickable = isCompleted || isCurrent;

            return (
              <button
                key={name}
                type="button"
                onClick={() => isClickable && onStepClick(stepNumber)}
                disabled={!isClickable}
                aria-label={`Go to step ${stepNumber}: ${name}`}
                className={cn(
                  "h-2 w-2 rounded-full transition-all",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500",
                  isCompleted
                    ? "bg-blue-600 cursor-pointer"
                    : isCurrent
                      ? "bg-blue-600 scale-125"
                      : "bg-foreground/20 cursor-default",
                )}
              />
            );
          })}
        </div>
      </div>
    </nav>
  );
}
