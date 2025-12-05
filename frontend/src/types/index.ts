// Patient Status Types
export type PatientStatus = 'active' | 'closed';

export type ClosureReason =
  | 'deceased'
  | 'cured'
  | 'remission'
  | 'transferred'
  | 'lost_to_followup'
  | 'patient_choice'
  | 'other';

export interface PatientClosure {
  reason: ClosureReason;
  notes?: string;
}

export interface PatientStatusUpdate {
  status: PatientStatus;
  closure?: PatientClosure;
}

// Patient Types
export interface Patient {
  id: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  sex: string;
  email?: string;
  phone?: string;
  cancer_details: CancerDetails;
  comorbidities: Comorbidity[];
  organ_function: OrganFunction[];
  ecog_status: number;
  current_medications: string[];
  allergies: string[];
  smoking_status?: string;
  pack_years?: number;
  genomic_report_id?: string;
  status?: PatientStatus;
  closure_reason?: ClosureReason;
  closure_notes?: string;
  closed_at?: string;
}

export interface CancerDetails {
  cancer_type: string;
  subtype?: string;
  stage: string;
  tnm_staging?: string;
  primary_site?: string;
  tumor_size_cm?: number;
  metastases: string[];
  histology?: string;
  grade?: string;
  diagnosis_date?: string;
}

export interface Comorbidity {
  condition: string;
  severity: string;
  treatment_implications: string[];
}

export interface OrganFunction {
  organ: string;
  status: string;
  key_values: Record<string, number>;
  notes?: string;
}

export interface PatientSummary {
  patient_id: string;
  name: string;
  age: number;
  cancer_type: string;
  stage: string;
  key_findings: string[];
}

// Genomics Types
export interface GenomicReport {
  report_id: string;
  patient_id: string;
  test_date: string;
  test_type: string;
  lab_name?: string;
  specimen_type: string;
  mutations: Mutation[];
  immunotherapy_markers?: ImmunotherapyMarkers;
  summary?: string;
}

export interface Mutation {
  gene: string;
  variant: string;
  classification: string;
  allele_frequency?: number;
  tier?: string;
  therapies: Therapy[];
}

export interface Therapy {
  drug_name: string;
  brand_name?: string;
  fda_approved: boolean;
  evidence_level?: string;
}

export interface ImmunotherapyMarkers {
  pdl1_expression?: number;
  pdl1_interpretation?: string;
  tmb?: number;
  tmb_interpretation?: string;
  msi_status?: string;
  immunotherapy_likely_benefit: boolean;
}

// Treatment Types
export interface TreatmentOption {
  id?: string;
  rank: number;
  name: string;
  treatment_name?: string;
  category?: string;
  treatment_type?: string;
  drugs?: string[];
  dosing?: string;
  description?: string;
  recommendation?: string;
  recommendation_level?: string;
  confidence?: number;
  confidence_score?: number;
  evidence_level?: string;
  expected_response_rate?: number;
  expected_outcomes?: Record<string, unknown>;
  key_trials?: string[];
  supporting_evidence?: string[];
  common_side_effects?: string[];
  contraindications?: string[];
  patient_specific_considerations?: string[];
  rationale?: string;
}

export interface ClinicalTrial {
  nct_id: string;
  title: string;
  brief_summary?: string;
  phase: string;
  status: string;
  sponsor?: string;
  interventions: string[];
  locations: string[];
  match_score: number;
  eligibility_criteria: EligibilityCriterion[];
  match_rationale?: string;
}

export interface EligibilityCriterion {
  criterion: string;
  inclusion: boolean;
  patient_meets?: boolean;
  details?: string;
}

export interface TreatmentPlan {
  id?: string;
  patient_id: string;
  generated_at: string;
  status?: string;
  primary_recommendation?: TreatmentOption;
  alternative_options?: TreatmentOption[];
  treatment_options: TreatmentOption[];
  clinical_trials: ClinicalTrial[];
  discussion_points: string[];
  summary?: string;
}

export interface TreatmentPlanResponse {
  plan: TreatmentPlan;
  requires_approval: boolean;
  approved_by?: string;
  approved_at?: string;
}

// Analysis Types
export interface AnalysisRequest {
  patient_id: string;
  analysis_type?: string;
  include_trials?: boolean;
  include_evidence?: boolean;
  user_questions?: string[];
  user_email?: string;
}

export interface AnalysisProgress {
  request_id: string;
  patient_id: string;
  status: string;
  current_step: string;
  progress_percent: number;
  steps_completed: string[];
  steps_remaining: string[];
  current_step_detail?: string;
  error_message?: string;
}

export interface AnalysisResult {
  request_id: string;
  patient_id: string;
  status: string;
  completed_at: string;
  summary: string;
  key_findings: string[];
  recommendations: string[];
  treatment_plan?: TreatmentPlan;
  clinical_trials: ClinicalTrial[];
  sources_used: string[];
}

// Chat Types
export interface ChatMessage {
  id: string;
  patient_id: string;
  timestamp: string;
  role: 'patient' | 'assistant' | 'system';
  content: string;
}

export interface ChatRequest {
  patient_id: string;
  message: string;
  context?: Record<string, unknown>;
}

export interface ChatResponse {
  patient_id: string;
  response: string;
  sources_used: string[];
  escalate_to_human: boolean;
  escalation_reason?: string;
  suggested_followup: string[];
}

// API Response Types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface APIError {
  detail: string;
  status_code: number;
}

// Treatment Cycle Types
export type TreatmentType =
  | 'chemotherapy'
  | 'immunotherapy'
  | 'targeted_therapy'
  | 'radiation'
  | 'surgery'
  | 'combination'
  | 'other';

export type TreatmentResponse = 'CR' | 'PR' | 'SD' | 'PD';

export type TreatmentCycleStatus = 'ongoing' | 'completed' | 'discontinued';

export interface TreatmentCycleCreate {
  treatment_name: string;
  treatment_type: TreatmentType;
  regimen?: string;
  cycle_number: number;
  start_date: string;
  dose?: string;
}

export interface TreatmentCycleUpdate {
  end_date?: string;
  dose_modification?: string;
  response?: TreatmentResponse;
  response_notes?: string;
  side_effects?: string[];
  status?: TreatmentCycleStatus;
  discontinuation_reason?: string;
}

export interface TreatmentCycle {
  id: string;
  patient_id: string;
  treatment_name: string;
  treatment_type: TreatmentType;
  regimen?: string;
  cycle_number: number;
  start_date: string;
  end_date?: string;
  dose?: string;
  dose_modification?: string;
  response?: TreatmentResponse;
  response_notes?: string;
  side_effects: string[];
  status: TreatmentCycleStatus;
  discontinuation_reason?: string;
  created_at: string;
  updated_at: string;
}

// Patient Event Types
export type PatientEventType =
  | 'diagnosis'
  | 'treatment_start'
  | 'treatment_end'
  | 'analysis'
  | 'status_change'
  | 'note'
  | 'other';

export interface PatientEvent {
  id: string;
  patient_id: string;
  event_type: PatientEventType;
  event_date: string;
  title: string;
  description?: string;
  reference_type?: string;
  reference_id?: string;
  created_at: string;
}

// Treatment Procedure Types
export type ProcedureType =
  | 'infusion'
  | 'lab_check'
  | 'imaging'
  | 'injection'
  | 'oral_medication'
  | 'radiation_session'
  | 'consultation'
  | 'other';

export type ProcedureStatus = 'scheduled' | 'completed' | 'missed' | 'cancelled';

export interface AdverseEvent {
  event: string;
  grade?: number; // CTCAE grade 1-5
  notes?: string;
}

export interface LabResult {
  value: number;
  unit: string;
  flag?: 'normal' | 'high' | 'low' | 'critical';
}

export interface ImagingResult {
  modality: string;
  findings?: string;
  impression?: string;
}

export interface TreatmentProcedureCreate {
  procedure_type: ProcedureType;
  procedure_name: string;
  day_number: number;
  scheduled_date: string;
  scheduled_time?: string;
  location?: string;
}

export interface TreatmentProcedureUpdate {
  status?: ProcedureStatus;
  actual_date?: string;
  actual_dose?: string;
  administered_by?: string;
  administration_notes?: string;
  adverse_events?: AdverseEvent[];
  lab_results?: Record<string, LabResult>;
  imaging_results?: ImagingResult;
  scheduled_time?: string;
  location?: string;
}

export interface TreatmentProcedure {
  id: string;
  treatment_cycle_id: string;
  patient_id: string;
  procedure_type: ProcedureType;
  procedure_name: string;
  day_number: number;
  scheduled_date: string;
  scheduled_time?: string;
  location?: string;
  status: ProcedureStatus;
  actual_date?: string;
  actual_dose?: string;
  administered_by?: string;
  administration_notes?: string;
  adverse_events: AdverseEvent[];
  lab_results?: Record<string, LabResult>;
  imaging_results?: ImagingResult;
  created_at: string;
  updated_at: string;
}

export interface ProcedureComplete {
  actual_date?: string;
  actual_dose?: string;
  administered_by?: string;
  administration_notes?: string;
  adverse_events?: AdverseEvent[];
  lab_results?: Record<string, LabResult>;
  imaging_results?: ImagingResult;
}

export interface ProcedureCancel {
  reason?: string;
}

export interface GenerateProceduresRequest {
  schedule_days: number[];
  procedure_type?: string;
  start_time?: string;
  location?: string;
}

// Clinical Notes Types
export type ClinicalNoteType =
  | 'general'
  | 'lab_result'
  | 'imaging'
  | 'treatment_response'
  | 'side_effect';

export interface ClinicalNoteCreate {
  note_text: string;
  note_type?: ClinicalNoteType;
  created_by?: string;
}

export interface ClinicalNote {
  id: string;
  patient_id: string;
  note_text: string;
  note_type: ClinicalNoteType;
  created_by?: string;
  created_at: string;
}

export interface ClinicalNotesResponse {
  notes: ClinicalNote[];
  total: number;
}
