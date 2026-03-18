"use client";

import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { FormField } from "@/components/ui/form-field";
import { TagInput } from "@/components/ui/tag-input";
import { useProfile } from "@/hooks/useProfile";

const preferencesSchema = z.object({
  desired_roles: z.array(z.string()),
  desired_locations: z.array(z.string()),
  min_salary: z.string(),
});

type PreferencesFormValues = z.infer<typeof preferencesSchema>;

export function PreferencesForm() {
  const { profile, updatePreferences } = useProfile();

  const {
    register,
    handleSubmit,
    control,
    formState: { errors, isSubmitting },
  } = useForm<PreferencesFormValues>({
    resolver: zodResolver(preferencesSchema),
    defaultValues: {
      desired_roles: profile?.desired_roles ?? [],
      desired_locations: profile?.desired_locations ?? [],
      min_salary: profile?.min_salary?.toString() ?? "",
    },
  });

  async function onSubmit(data: PreferencesFormValues) {
    const salary = data.min_salary ? Number(data.min_salary) : null;
    if (salary !== null && (isNaN(salary) || salary < 0)) {
      toast.error("Salary must be a positive number.");
      return;
    }
    try {
      await updatePreferences.mutateAsync({
        desired_roles: data.desired_roles,
        desired_locations: data.desired_locations,
        min_salary: salary,
      });
      toast.success("Preferences updated successfully.");
    } catch {
      toast.error("Failed to update preferences. Please try again.");
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6" noValidate>
      <FormField
        label="Desired Roles"
        htmlFor="desired_roles"
        error={errors.desired_roles?.message}
      >
        <Controller
          name="desired_roles"
          control={control}
          render={({ field }) => (
            <TagInput
              id="desired_roles"
              value={field.value}
              onChange={field.onChange}
              placeholder="e.g. Frontend Engineer, Product Manager..."
            />
          )}
        />
      </FormField>

      <FormField
        label="Desired Locations"
        htmlFor="desired_locations"
        error={errors.desired_locations?.message}
      >
        <Controller
          name="desired_locations"
          control={control}
          render={({ field }) => (
            <TagInput
              id="desired_locations"
              value={field.value}
              onChange={field.onChange}
              placeholder="e.g. San Francisco, Remote, New York..."
            />
          )}
        />
      </FormField>

      <FormField
        label="Minimum Salary (USD)"
        htmlFor="min_salary"
        error={errors.min_salary?.message}
      >
        <Input
          id="min_salary"
          type="number"
          min={0}
          placeholder="80000"
          error={!!errors.min_salary}
          {...register("min_salary")}
        />
      </FormField>

      <div className="flex justify-end">
        <Button type="submit" loading={isSubmitting}>
          Save Preferences
        </Button>
      </div>
    </form>
  );
}
