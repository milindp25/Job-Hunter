"use client";

import { useCallback } from "react";
import { Plus, Trash2, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import type { Skill } from "@/lib/types";
import type { OnboardingStepProps } from "../onboarding-types";

const SKILL_LEVELS: { value: Skill["level"]; label: string }[] = [
  { value: "beginner", label: "Beginner" },
  { value: "intermediate", label: "Intermediate" },
  { value: "advanced", label: "Advanced" },
  { value: "expert", label: "Expert" },
];

function createEmptySkill(): Skill {
  return { name: "", level: "intermediate", years: 1 };
}

export function SkillsStep({ data, onUpdate, resumeData }: OnboardingStepProps) {
  const skills = data.skills.skills;

  const updateSkills = useCallback(
    (newSkills: Skill[]) => {
      onUpdate({ skills: { skills: newSkills } });
    },
    [onUpdate],
  );

  const addSkill = useCallback(() => {
    updateSkills([...skills, createEmptySkill()]);
  }, [skills, updateSkills]);

  const removeSkill = useCallback(
    (index: number) => {
      updateSkills(skills.filter((_, i) => i !== index));
    },
    [skills, updateSkills],
  );

  const updateSkill = useCallback(
    (index: number, field: keyof Skill, value: string | number) => {
      const updated = skills.map((skill, i) =>
        i === index ? { ...skill, [field]: value } : skill,
      );
      updateSkills(updated);
    },
    [skills, updateSkills],
  );

  const isAutoFilled = resumeData?.skills && resumeData.skills.length > 0;

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h2 className="text-xl font-bold text-foreground">
          Skills &amp; Expertise
        </h2>
        <p className="text-sm text-foreground/60">
          Add your technical and professional skills. This helps us match you
          with the right opportunities.
        </p>
        {isAutoFilled && (
          <p className="text-xs text-blue-600 dark:text-blue-400">
            Skills have been pre-filled from your resume. Feel free to edit or
            add more.
          </p>
        )}
      </div>

      {/* Skill entries */}
      <div className="space-y-4">
        {skills.map((skill, index) => (
          <div
            key={index}
            className="flex flex-col gap-3 rounded-lg border border-foreground/10 p-4 sm:flex-row sm:items-end"
          >
            {/* Skill name */}
            <div className="flex-1 space-y-1.5">
              <Label htmlFor={`skill-name-${index}`}>Skill</Label>
              <Input
                id={`skill-name-${index}`}
                placeholder="e.g. JavaScript, Project Management"
                value={skill.name}
                onChange={(e) => updateSkill(index, "name", e.target.value)}
              />
            </div>

            {/* Level */}
            <div className="w-full space-y-1.5 sm:w-40">
              <Label htmlFor={`skill-level-${index}`}>Level</Label>
              <Select
                id={`skill-level-${index}`}
                value={skill.level}
                onChange={(e) =>
                  updateSkill(index, "level", e.target.value)
                }
              >
                {SKILL_LEVELS.map((level) => (
                  <option key={level.value} value={level.value}>
                    {level.label}
                  </option>
                ))}
              </Select>
            </div>

            {/* Years */}
            <div className="w-full space-y-1.5 sm:w-28">
              <Label htmlFor={`skill-years-${index}`}>Years</Label>
              <Input
                id={`skill-years-${index}`}
                type="number"
                min={0}
                max={50}
                value={skill.years}
                onChange={(e) =>
                  updateSkill(
                    index,
                    "years",
                    Math.max(0, parseInt(e.target.value, 10) || 0),
                  )
                }
              />
            </div>

            {/* Remove button */}
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={() => removeSkill(index)}
              aria-label={`Remove skill: ${skill.name || `skill ${index + 1}`}`}
              className="shrink-0 text-red-500 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/20"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        ))}
      </div>

      {/* Add skill button */}
      <Button
        type="button"
        variant="outline"
        onClick={addSkill}
        className="w-full"
      >
        <Plus className="h-4 w-4" />
        Add Skill
      </Button>

      {/* Empty state warning */}
      {skills.length === 0 && (
        <div className="flex items-center gap-2 rounded-lg bg-amber-50 p-3 text-sm text-amber-700 dark:bg-amber-950/20 dark:text-amber-300">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          <span>
            Adding at least one skill is recommended to help us find the best
            matches for you.
          </span>
        </div>
      )}

      <p className="text-center text-sm text-foreground/50">
        Almost there! Your skills help employers understand your expertise.
      </p>
    </div>
  );
}
