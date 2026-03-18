"use client";

import { useFieldArray, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { useProfile } from "@/hooks/useProfile";

const experienceSchema = z.object({
  company: z.string().min(1, "Company name is required"),
  title: z.string().min(1, "Job title is required"),
  description: z.string(),
  start_date: z.string().min(1, "Start date is required"),
  end_date: z.string(),
});

const experienceFormSchema = z.object({
  experiences: z.array(experienceSchema),
});

type ExperienceFormValues = z.infer<typeof experienceFormSchema>;

const EMPTY_EXPERIENCE = {
  company: "",
  title: "",
  description: "",
  start_date: "",
  end_date: "",
};

export function ExperienceForm() {
  const { profile, updateExperience } = useProfile();

  const {
    register,
    handleSubmit,
    control,
    formState: { errors, isSubmitting },
  } = useForm<ExperienceFormValues>({
    resolver: zodResolver(experienceFormSchema),
    defaultValues: {
      experiences:
        profile?.experience && profile.experience.length > 0
          ? profile.experience.map((exp) => ({
              company: exp.company,
              title: exp.title,
              description: exp.description ?? "",
              start_date: exp.start_date,
              end_date: exp.end_date ?? "",
            }))
          : [EMPTY_EXPERIENCE],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: "experiences",
  });

  async function onSubmit(data: ExperienceFormValues) {
    try {
      const payload = data.experiences.map((exp) => ({
        company: exp.company,
        title: exp.title,
        description: exp.description,
        start_date: exp.start_date,
        end_date: exp.end_date || null,
      }));
      await updateExperience.mutateAsync(payload);
      toast.success("Experience updated successfully.");
    } catch {
      toast.error("Failed to update experience. Please try again.");
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6" noValidate>
      <div className="space-y-6">
        {fields.map((field, index) => (
          <div
            key={field.id}
            className="space-y-4 rounded-lg border border-foreground/10 p-4"
          >
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-foreground/70">
                Experience {index + 1}
              </span>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="text-red-500 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950"
                onClick={() => remove(index)}
                disabled={fields.length <= 1}
                aria-label={`Remove experience ${index + 1}`}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor={`experiences.${index}.company`}>Company</Label>
                <Input
                  id={`experiences.${index}.company`}
                  placeholder="Acme Corp"
                  error={!!errors.experiences?.[index]?.company}
                  {...register(`experiences.${index}.company`)}
                />
                {errors.experiences?.[index]?.company && (
                  <p className="text-sm text-red-500" role="alert">
                    {errors.experiences[index].company.message}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor={`experiences.${index}.title`}>Job Title</Label>
                <Input
                  id={`experiences.${index}.title`}
                  placeholder="Software Engineer"
                  error={!!errors.experiences?.[index]?.title}
                  {...register(`experiences.${index}.title`)}
                />
                {errors.experiences?.[index]?.title && (
                  <p className="text-sm text-red-500" role="alert">
                    {errors.experiences[index].title.message}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor={`experiences.${index}.start_date`}>
                  Start Date
                </Label>
                <Input
                  id={`experiences.${index}.start_date`}
                  type="date"
                  error={!!errors.experiences?.[index]?.start_date}
                  {...register(`experiences.${index}.start_date`)}
                />
                {errors.experiences?.[index]?.start_date && (
                  <p className="text-sm text-red-500" role="alert">
                    {errors.experiences[index].start_date.message}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor={`experiences.${index}.end_date`}>
                  End Date
                </Label>
                <Input
                  id={`experiences.${index}.end_date`}
                  type="date"
                  {...register(`experiences.${index}.end_date`)}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor={`experiences.${index}.description`}>
                Description
              </Label>
              <Textarea
                id={`experiences.${index}.description`}
                rows={3}
                placeholder="Describe your responsibilities and achievements..."
                {...register(`experiences.${index}.description`)}
              />
            </div>
          </div>
        ))}
      </div>

      <div className="flex items-center justify-between">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => append(EMPTY_EXPERIENCE)}
        >
          <Plus className="h-4 w-4" />
          Add Experience
        </Button>

        <Button type="submit" loading={isSubmitting}>
          Save Experience
        </Button>
      </div>
    </form>
  );
}
