"use client";

import { useFieldArray, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useProfile } from "@/hooks/useProfile";

const educationSchema = z.object({
  institution: z.string().min(1, "Institution is required"),
  degree: z.string().min(1, "Degree is required"),
  field: z.string().min(1, "Field of study is required"),
  start_date: z.string().min(1, "Start date is required"),
  end_date: z.string(),
});

const educationFormSchema = z.object({
  entries: z.array(educationSchema),
});

type EducationFormValues = z.infer<typeof educationFormSchema>;

const EMPTY_EDUCATION = {
  institution: "",
  degree: "",
  field: "",
  start_date: "",
  end_date: "",
};

export function EducationForm() {
  const { profile, updateEducation } = useProfile();

  const {
    register,
    handleSubmit,
    control,
    formState: { errors, isSubmitting },
  } = useForm<EducationFormValues>({
    resolver: zodResolver(educationFormSchema),
    defaultValues: {
      entries:
        profile?.education && profile.education.length > 0
          ? profile.education.map((edu) => ({
              institution: edu.institution,
              degree: edu.degree,
              field: edu.field,
              start_date: edu.start_date,
              end_date: edu.end_date ?? "",
            }))
          : [EMPTY_EDUCATION],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: "entries",
  });

  async function onSubmit(data: EducationFormValues) {
    try {
      const payload = data.entries.map((entry) => ({
        institution: entry.institution,
        degree: entry.degree,
        field: entry.field,
        start_date: entry.start_date,
        end_date: entry.end_date || null,
      }));
      await updateEducation.mutateAsync(payload);
      toast.success("Education updated successfully.");
    } catch {
      toast.error("Failed to update education. Please try again.");
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
                Education {index + 1}
              </span>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="text-red-500 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950"
                onClick={() => remove(index)}
                disabled={fields.length <= 1}
                aria-label={`Remove education ${index + 1}`}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor={`entries.${index}.institution`}>
                  Institution
                </Label>
                <Input
                  id={`entries.${index}.institution`}
                  placeholder="MIT"
                  error={!!errors.entries?.[index]?.institution}
                  {...register(`entries.${index}.institution`)}
                />
                {errors.entries?.[index]?.institution && (
                  <p className="text-sm text-red-500" role="alert">
                    {errors.entries[index].institution.message}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor={`entries.${index}.degree`}>Degree</Label>
                <Input
                  id={`entries.${index}.degree`}
                  placeholder="Bachelor of Science"
                  error={!!errors.entries?.[index]?.degree}
                  {...register(`entries.${index}.degree`)}
                />
                {errors.entries?.[index]?.degree && (
                  <p className="text-sm text-red-500" role="alert">
                    {errors.entries[index].degree.message}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor={`entries.${index}.field`}>Field of Study</Label>
                <Input
                  id={`entries.${index}.field`}
                  placeholder="Computer Science"
                  error={!!errors.entries?.[index]?.field}
                  {...register(`entries.${index}.field`)}
                />
                {errors.entries?.[index]?.field && (
                  <p className="text-sm text-red-500" role="alert">
                    {errors.entries[index].field.message}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor={`entries.${index}.start_date`}>
                  Start Date
                </Label>
                <Input
                  id={`entries.${index}.start_date`}
                  type="date"
                  error={!!errors.entries?.[index]?.start_date}
                  {...register(`entries.${index}.start_date`)}
                />
                {errors.entries?.[index]?.start_date && (
                  <p className="text-sm text-red-500" role="alert">
                    {errors.entries[index].start_date.message}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor={`entries.${index}.end_date`}>End Date</Label>
                <Input
                  id={`entries.${index}.end_date`}
                  type="date"
                  {...register(`entries.${index}.end_date`)}
                />
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="flex items-center justify-between">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => append(EMPTY_EDUCATION)}
        >
          <Plus className="h-4 w-4" />
          Add Education
        </Button>

        <Button type="submit" loading={isSubmitting}>
          Save Education
        </Button>
      </div>
    </form>
  );
}
