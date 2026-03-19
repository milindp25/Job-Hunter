export interface User {
  id: string;
  email: string;
  full_name: string;
  avatar_url: string | null;
  auth_provider: "email" | "google" | "github" | "linkedin";
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserProfile {
  id: string;
  user_id: string;
  phone: string | null;
  location: string | null;
  linkedin_url: string | null;
  github_url: string | null;
  portfolio_url: string | null;
  years_of_experience: number | null;
  desired_roles: string[];
  desired_locations: string[];
  min_salary: number | null;
  skills: Skill[];
  education: Education[];
  experience: Experience[];
  certifications: string[];
  languages: Language[];
  summary: string | null;
  onboarding_completed: boolean;
  profile_completeness: number;
}

export interface Skill {
  name: string;
  level: "beginner" | "intermediate" | "advanced" | "expert";
  years: number;
}

export interface Education {
  institution: string;
  degree: string;
  field: string;
  start_date: string;
  end_date: string | null;
}

export interface Experience {
  company: string;
  title: string;
  description: string;
  start_date: string;
  end_date: string | null;
}

export interface Language {
  language: string;
  proficiency: "basic" | "conversational" | "professional" | "native";
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface UserWithProfile {
  user: User;
  profile: UserProfile;
}

export interface ProfileUpdatePayload {
  phone?: string | null;
  location?: string | null;
  linkedin_url?: string | null;
  github_url?: string | null;
  portfolio_url?: string | null;
  summary?: string | null;
  years_of_experience?: number | null;
}

export interface PreferencesUpdatePayload {
  desired_roles?: string[];
  desired_locations?: string[];
  min_salary?: number | null;
}

export interface ApiError {
  error: {
    code: string;
    detail: string;
  };
}

export interface Resume {
  id: string;
  user_id: string;
  filename: string;
  file_size: number;
  file_type: "pdf" | "docx";
  is_primary: boolean;
  parsed_data: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface ResumeListResponse {
  resumes: Resume[];
  total: number;
}

export interface ResumeUploadResponse {
  resume: Resume;
  message: string;
}

export interface ResumeDownloadResponse {
  download_url: string;
  filename: string;
  expires_in: number;
}

export interface Job {
  id: string;
  external_id: string;
  source: string;
  title: string;
  company: string;
  location: string | null;
  is_remote: boolean;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string | null;
  description: string;
  job_type: string;
  url: string;
  tags: string[];
  posted_at: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface JobListResponse {
  jobs: Job[];
  total: number;
  page: number;
  page_size: number;
}

export interface SavedJob {
  id: string;
  job: Job;
  saved_at: string;
  notes: string | null;
}

export interface SavedJobListResponse {
  saved_jobs: SavedJob[];
  total: number;
}

export interface JobSearchParams {
  query?: string;
  location?: string;
  salary_min?: number;
  salary_max?: number;
  job_type?: string;
  source?: string;
  is_remote?: boolean;
  page?: number;
  page_size?: number;
}

export interface JobFetchResponse {
  sources_fetched: string[];
  total_new_jobs: number;
  total_updated_jobs: number;
  message: string;
}
