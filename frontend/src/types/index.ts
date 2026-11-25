export type AgentEvent = {
  type: string;
  node: string;
  timestamp?: string;
  duration_ms?: number;
  attempt?: number;
  message?: string;
  analysis?: Analysis;
};
export type Requirement = {
  requirement: string;
  category: string;
  status: string;
  evidence: string;
  explanation: string;
};
export type Review = {
  approved: boolean;
  quality_score: number;
  issues: string[];
  unsupported_claims: string[];
  suggestions: string[];
  revision_required: boolean;
};
export type Materials = {
  subject: string;
  email: string;
  cover_letter: string;
  professional_summary: string;
  resume_suggestions: string[];
  keywords: string[];
  project_suggestions: string[];
  interview_questions: string[];
  claims: { claim: string; evidence: string }[];
};
export type Profile = {
  candidate_name: string;
  email: string;
  education: string[];
  technical_skills: string[];
  projects: string[];
  experience: string[];
  certifications: string[];
  achievements: string[];
  missing_information: string[];
};
export type Job = {
  job_title: string;
  company: string;
  required_skills: string[];
  preferred_skills: string[];
  responsibilities: string[];
  education_requirements: string[];
  ambiguities: string[];
};
export type Analysis = {
  id: string;
  application_id: string;
  application_status: string;
  job_title: string;
  company: string;
  created_at: string;
  match_score: number | null;
  workflow_status: string;
  result: {
    mode?: string;
    resume?: Profile;
    job?: Job;
    matching?: {
      notice?: string;
      requirements: Requirement[];
      breakdown: Record<
        string,
        { coverage: number | null; weight: number; count: number; contribution: number }
      >;
      recommendations: string[];
      project_relevance: string[];
      experience_analysis: string;
    };
    application?: Materials;
    review?: Review;
    events?: AgentEvent[];
    errors?: string[];
    revision_count?: number;
  };
};
export type Health = {
  status: string;
  database: string;
  version: string;
  llm_mode: string;
  model: string;
  tracing: boolean;
  max_revisions: number;
  max_upload_mb: number;
};
