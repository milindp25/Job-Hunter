"use client";

import { useFieldArray, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { useProfile } from "@/hooks/useProfile";

const skillSchema = z.object({
  name: z.string().min(1, "Skill name is required"),
  level: z.enum(["beginner", "intermediate", "advanced", "expert"]),
  years: z.string().min(1, "Required"),
});

const skillsFormSchema = z.object({
  skills: z.array(skillSchema),
});

type SkillsFormValues = z.infer<typeof skillsFormSchema>;

const EMPTY_SKILL = { name: "", level: "intermediate" as const, years: "0" };

export function SkillsForm() {
  const { profile, updateSkills } = useProfile();

  const {
    register,
    handleSubmit,
    control,
    formState: { errors, isSubmitting },
  } = useForm<SkillsFormValues>({
    resolver: zodResolver(skillsFormSchema),
    defaultValues: {
      skills:
        profile?.skills && profile.skills.length > 0
          ? profile.skills.map((s) => ({ ...s, years: String(s.years) }))
          : [EMPTY_SKILL],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: "skills",
  });

  async function onSubmit(data: SkillsFormValues) {
    try {
      const payload = data.skills.map((s) => ({
        name: s.name,
        level: s.level,
        years: Number(s.years) || 0,
      }));
      await updateSkills.mutateAsync(payload);
      toast.success("Skills updated successfully.");
    } catch {
      toast.error("Failed to update skills. Please try again.");
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6" noValidate>
      <div className="space-y-4">
        {fields.map((field, index) => (
          <div
            key={field.id}
            className="flex flex-col gap-4 rounded-lg border border-foreground/10 p-4 sm:flex-row sm:items-end"
          >
            <div className="flex-1 space-y-2">
              <Label htmlFor={`skills.${index}.name`}>Skill Name</Label>
              <Input
                id={`skills.${index}.name`}
                placeholder="e.g. React, Python, AWS"
                error={!!errors.skills?.[index]?.name}
                {...register(`skills.${index}.name`)}
              />
              {errors.skills?.[index]?.name && (
                <p className="text-sm text-red-500" role="alert">
                  {errors.skills[index].name.message}
                </p>
              )}
            </div>

            <div className="w-full space-y-2 sm:w-40">
              <Label htmlFor={`skills.${index}.level`}>Level</Label>
              <Select
                id={`skills.${index}.level`}
                error={!!errors.skills?.[index]?.level}
                {...register(`skills.${index}.level`)}
              >
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
                <option value="expert">Expert</option>
              </Select>
            </div>

            <div className="w-full space-y-2 sm:w-24">
              <Label htmlFor={`skills.${index}.years`}>Years</Label>
              <Input
                id={`skills.${index}.years`}
                type="number"
                min={0}
                max={50}
                error={!!errors.skills?.[index]?.years}
                {...register(`skills.${index}.years`)}
              />
            </div>

            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="shrink-0 text-red-500 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950"
              onClick={() => remove(index)}
              disabled={fields.length <= 1}
              aria-label={`Remove skill ${index + 1}`}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        ))}
      </div>

      <div className="flex items-center justify-between">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => append(EMPTY_SKILL)}
        >
          <Plus className="h-4 w-4" />
          Add Skill
        </Button>

        <Button type="submit" loading={isSubmitting}>
          Save Skills
        </Button>
      </div>
    </form>
  );
}
