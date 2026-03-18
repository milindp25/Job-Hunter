"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { FormField } from "@/components/ui/form-field";
import { useProfile } from "@/hooks/useProfile";

const urlOrEmpty = z.union([z.string().url("Please enter a valid URL"), z.literal("")]);

const personalInfoSchema = z.object({
  phone: z.string(),
  location: z.string(),
  linkedin_url: urlOrEmpty,
  github_url: urlOrEmpty,
  portfolio_url: urlOrEmpty,
  summary: z.string(),
  years_of_experience: z.string(),
});

type PersonalInfoValues = z.infer<typeof personalInfoSchema>;

export function PersonalInfoForm() {
  const { profile, updateProfile } = useProfile();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<PersonalInfoValues>({
    resolver: zodResolver(personalInfoSchema),
    defaultValues: {
      phone: profile?.phone ?? "",
      location: profile?.location ?? "",
      linkedin_url: profile?.linkedin_url ?? "",
      github_url: profile?.github_url ?? "",
      portfolio_url: profile?.portfolio_url ?? "",
      summary: profile?.summary ?? "",
      years_of_experience: profile?.years_of_experience?.toString() ?? "",
    },
  });

  async function onSubmit(data: PersonalInfoValues) {
    const years = data.years_of_experience ? Number(data.years_of_experience) : null;
    if (years !== null && (isNaN(years) || years < 0 || years > 50)) {
      toast.error("Years of experience must be between 0 and 50.");
      return;
    }
    try {
      await updateProfile.mutateAsync({
        phone: data.phone || null,
        location: data.location || null,
        linkedin_url: data.linkedin_url || null,
        github_url: data.github_url || null,
        portfolio_url: data.portfolio_url || null,
        summary: data.summary || null,
        years_of_experience: years,
      });
      toast.success("Personal information updated successfully.");
    } catch {
      toast.error("Failed to update personal information. Please try again.");
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6" noValidate>
      <div className="grid gap-6 sm:grid-cols-2">
        <FormField label="Phone" htmlFor="phone" error={errors.phone?.message}>
          <Input
            id="phone"
            type="tel"
            placeholder="+1 (555) 123-4567"
            error={!!errors.phone}
            {...register("phone")}
          />
        </FormField>

        <FormField
          label="Location"
          htmlFor="location"
          error={errors.location?.message}
        >
          <Input
            id="location"
            placeholder="San Francisco, CA"
            error={!!errors.location}
            {...register("location")}
          />
        </FormField>

        <FormField
          label="Years of Experience"
          htmlFor="years_of_experience"
          error={errors.years_of_experience?.message}
        >
          <Input
            id="years_of_experience"
            type="number"
            min={0}
            max={50}
            placeholder="5"
            error={!!errors.years_of_experience}
            {...register("years_of_experience")}
          />
        </FormField>
      </div>

      <div className="grid gap-6 sm:grid-cols-2">
        <FormField
          label="LinkedIn URL"
          htmlFor="linkedin_url"
          error={errors.linkedin_url?.message}
        >
          <Input
            id="linkedin_url"
            type="url"
            placeholder="https://linkedin.com/in/username"
            error={!!errors.linkedin_url}
            {...register("linkedin_url")}
          />
        </FormField>

        <FormField
          label="GitHub URL"
          htmlFor="github_url"
          error={errors.github_url?.message}
        >
          <Input
            id="github_url"
            type="url"
            placeholder="https://github.com/username"
            error={!!errors.github_url}
            {...register("github_url")}
          />
        </FormField>

        <FormField
          label="Portfolio URL"
          htmlFor="portfolio_url"
          error={errors.portfolio_url?.message}
        >
          <Input
            id="portfolio_url"
            type="url"
            placeholder="https://yourportfolio.com"
            error={!!errors.portfolio_url}
            {...register("portfolio_url")}
          />
        </FormField>
      </div>

      <FormField
        label="Professional Summary"
        htmlFor="summary"
        error={errors.summary?.message}
      >
        <Textarea
          id="summary"
          rows={4}
          placeholder="A brief summary of your professional background and career goals..."
          error={!!errors.summary}
          {...register("summary")}
        />
      </FormField>

      <div className="flex justify-end">
        <Button type="submit" loading={isSubmitting}>
          Save Changes
        </Button>
      </div>
    </form>
  );
}
