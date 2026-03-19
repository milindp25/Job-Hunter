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

export interface JobMatchScore {
  id: string;
  job_id: string;
  overall_score: number;
  keyword_score: number;
  ai_score: number | null;
  skills_match: number | null;
  experience_match: number | null;
  education_match: number | null;
  location_match: number | null;
  salary_match: number | null;
  strengths: string[];
  gaps: string[];
  recommendation: string | null;
  created_at: string;
  updated_at: string;
}

export interface JobMatchWithJob {
  match: JobMatchScore;
  job: Job;
}

export interface MatchResultsResponse {
  matches: JobMatchWithJob[];
  total: number;
  page: number;
  page_size: number;
}

export interface MatchAnalyzeResponse {
  total_jobs_analyzed: number;
  new_matches: number;
  updated_matches: number;
  top_score: number;
  message: string;
}

export interface SingleMatchAnalyzeResponse {
  match: JobMatchScore;
  message: string;
}

// -- ATS Compliance Checker --

export interface AtsFinding {
  id: string;
  category: 'format' | 'keyword' | 'content';
  severity: 'blocker' | 'critical' | 'warning' | 'info';
  confidence: 'high' | 'medium' | 'low';
  rule_id: string;
  title: string;
  detail: string;
  suggestion: string;
  section: string | null;
  metadata: Record<string, string | number | boolean | null>;
  dismissed: boolean;
}

export interface AtsSuggestion {
  section: string;
  before: string;
  after: string;
  reason: string;
  estimated_impact: string;
}

export interface AtsCheck {
  id: string;
  resume_id: string;
  job_id: string | null;
  check_type: 'format_only' | 'full';
  overall_score: number;
  format_score: number;
  keyword_score: number | null;
  content_score: number | null;
  findings: AtsFinding[];
  suggestions: AtsSuggestion[];
  ai_analysis_available: boolean;
  is_stale: boolean;
  created_at: string;
  updated_at: string;
}

export interface AtsCheckListResponse {
  checks: AtsCheck[];
  total: number;
  page: number;
  page_size: number;
}

// -- Resume Generator --

export interface ResumeTemplate {
  id: string;
  name: string;
  description: string;
}

export interface ResumeTemplatesResponse {
  templates: ResumeTemplate[];
}

// -- Tailored Resume --

export interface TailoredResume {
  id: string;
  resume_id: string;
  job_id: string;
  tailored_summary: string | null;
  tailored_experience: Record<string, unknown>[];
  tailored_skills: string[];
  keyword_matches: string[];
  keyword_gaps: string[];
  match_score_before: number | null;
  match_score_after: number | null;
  ai_model: string;
  created_at: string;
}

export interface TailoredResumeListResponse {
  items: TailoredResume[];
  total: number;
}


// -- Dashboard --

export interface DashboardStats {
  total_saved_jobs: number;
  total_matches: number;
  resumes_count: number;
  avg_match_score: number | null;
  avg_ats_score: number | null;
  recent_matches: RecentMatch[];
  weekly_activity: ActivityPoint[];
}

export interface RecentMatch {
  job_title: string;
  company: string;
  score: number;
  matched_at: string | null;
}

export interface ActivityPoint {
  date: string;
  matches: number;
  saved: number;
}
