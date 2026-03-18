import type { Skill, Education, Experience } from "@/lib/types";

export const STEP_NAMES = [
  "Resume",
  "Personal",
  "Skills",
  "Experience",
  "Education",
  "Preferences",
  "Review",
] as const;

export const TOTAL_STEPS = STEP_NAMES.length;

export type StepName = (typeof STEP_NAMES)[number];

export interface ResumeData {
  full_name?: string;
  phone?: string;
  location?: string;
  linkedin_url?: string;
  github_url?: string;
  portfolio_url?: string;
  summary?: string;
  skills?: Skill[];
  experience?: Experience[];
  education?: Education[];
  certifications?: string[];
}

export interface PersonalInfoData {
  full_name: string;
  phone: string;
  location: string;
  linkedin_url: string;
  github_url: string;
  portfolio_url: string;
  summary: string;
}

export interface SkillsData {
  skills: Skill[];
}

export interface ExperienceData {
  experience: Experience[];
}

export interface EducationData {
  education: Education[];
  certifications: string[];
}

export interface PreferencesData {
  desired_roles: string[];
  desired_locations: string[];
  min_salary: number | null;
  job_types: string[];
}

export interface OnboardingData {
  resumeData: ResumeData | null;
  personalInfo: PersonalInfoData;
  skills: SkillsData;
  experience: ExperienceData;
  education: EducationData;
  preferences: PreferencesData;
  linkedinUrl: string;
}

export interface OnboardingStepProps {
  data: OnboardingData;
  onUpdate: (updates: Partial<OnboardingData>) => void;
  resumeData: ResumeData | null;
}

/** Set of field keys that were pre-filled from resume parsing. */
export type AutoFilledFields = Set<string>;
