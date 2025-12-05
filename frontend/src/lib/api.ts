import axios, { AxiosError, AxiosInstance, AxiosResponse } from 'axios';
import type {
  Patient,
  PatientSummary,
  PatientStatusUpdate,
  PatientEvent,
  GenomicReport,
  TreatmentPlan,
  TreatmentPlanResponse,
  TreatmentCycle,
  TreatmentCycleCreate,
  TreatmentCycleUpdate,
  TreatmentProcedure,
  TreatmentProcedureCreate,
  TreatmentProcedureUpdate,
  ProcedureComplete,
  ProcedureCancel,
  ClinicalTrial,
  AnalysisRequest,
  AnalysisProgress,
  AnalysisResult,
  ChatRequest,
  ChatResponse,
  PaginatedResponse,
  APIError,
  ClinicalNote,
  ClinicalNoteCreate,
  ClinicalNotesResponse,
} from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Token getter function type - will be set by the auth provider
type TokenGetter = () => Promise<string | null>;

class ApiClient {
  private client: AxiosInstance;
  private getToken: TokenGetter | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_BASE_URL}/api/v1`,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000,
    });

    // Request interceptor for auth token
    this.client.interceptors.request.use(
      async (config) => {
        if (this.getToken) {
          try {
            const token = await this.getToken();
            if (token) {
              config.headers.Authorization = `Bearer ${token}`;
            }
          } catch (error) {
            // Token fetch failed, continue without auth
            console.warn('Failed to get auth token:', error);
          }
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<APIError>) => {
        const apiError: APIError = {
          detail: error.response?.data?.detail || error.message || 'An error occurred',
          status_code: error.response?.status || 500,
        };
        return Promise.reject(apiError);
      }
    );
  }

  /**
   * Set the token getter function for authentication.
   * This should be called from a component that has access to Clerk's useAuth hook.
   */
  setTokenGetter(getter: TokenGetter) {
    this.getToken = getter;
  }

  // Patients
  async getPatients(params?: {
    page?: number;
    page_size?: number;
    cancer_type?: string;
    search?: string;
  }): Promise<PaginatedResponse<Patient>> {
    const response = await this.client.get<PaginatedResponse<Patient>>('/patients', { params });
    return response.data;
  }

  async getPatient(patientId: string): Promise<Patient> {
    const response = await this.client.get<Patient>(`/patients/${patientId}`);
    return response.data;
  }

  async getPatientSummary(patientId: string): Promise<PatientSummary> {
    const response = await this.client.get<PatientSummary>(`/patients/${patientId}/summary`);
    return response.data;
  }

  async createPatient(patient: Omit<Patient, 'id'>): Promise<Patient> {
    const response = await this.client.post<Patient>('/patients', patient);
    return response.data;
  }

  async updatePatient(patientId: string, patient: Partial<Patient>): Promise<Patient> {
    const response = await this.client.put<Patient>(`/patients/${patientId}`, patient);
    return response.data;
  }

  async deletePatient(patientId: string): Promise<void> {
    await this.client.delete(`/patients/${patientId}`);
  }

  async updatePatientStatus(patientId: string, statusUpdate: PatientStatusUpdate): Promise<Patient> {
    const response = await this.client.patch<Patient>(`/patients/${patientId}/status`, statusUpdate);
    return response.data;
  }

  async getPatientStatus(patientId: string): Promise<{
    patient_id: string;
    status: string;
    closure_reason?: string;
    closure_notes?: string;
    closed_at?: string;
  }> {
    const response = await this.client.get(`/patients/${patientId}/status`);
    return response.data;
  }

  async getPatientTimeline(patientId: string, limit?: number): Promise<PatientEvent[]> {
    const response = await this.client.get<PatientEvent[]>(`/patients/${patientId}/timeline`, {
      params: { limit },
    });
    return response.data;
  }

  // Treatment Cycles
  async getTreatmentCycles(patientId: string, status?: string, limit?: number): Promise<TreatmentCycle[]> {
    const response = await this.client.get<TreatmentCycle[]>(`/treatment-cycles/patients/${patientId}`, {
      params: { status, limit },
    });
    return response.data;
  }

  async getTreatmentCycle(cycleId: string): Promise<TreatmentCycle> {
    const response = await this.client.get<TreatmentCycle>(`/treatment-cycles/${cycleId}`);
    return response.data;
  }

  async createTreatmentCycle(patientId: string, cycle: TreatmentCycleCreate): Promise<TreatmentCycle> {
    const response = await this.client.post<TreatmentCycle>(`/treatment-cycles/patients/${patientId}`, cycle);
    return response.data;
  }

  async updateTreatmentCycle(cycleId: string, update: TreatmentCycleUpdate): Promise<TreatmentCycle> {
    const response = await this.client.patch<TreatmentCycle>(`/treatment-cycles/${cycleId}`, update);
    return response.data;
  }

  async deleteTreatmentCycle(cycleId: string): Promise<void> {
    await this.client.delete(`/treatment-cycles/${cycleId}`);
  }

  // Treatment Procedures
  async getProcedures(cycleId: string, status?: string, limit?: number): Promise<TreatmentProcedure[]> {
    const response = await this.client.get<TreatmentProcedure[]>(`/treatment-cycles/${cycleId}/procedures`, {
      params: { status, limit },
    });
    return response.data;
  }

  async getProcedure(procedureId: string): Promise<TreatmentProcedure> {
    const response = await this.client.get<TreatmentProcedure>(`/procedures/${procedureId}`);
    return response.data;
  }

  async getPatientProcedures(patientId: string, params?: {
    status?: string;
    procedure_type?: string;
    limit?: number;
  }): Promise<TreatmentProcedure[]> {
    const response = await this.client.get<TreatmentProcedure[]>(`/patients/${patientId}/procedures`, { params });
    return response.data;
  }

  async getUpcomingProcedures(patientId: string, daysAhead?: number): Promise<TreatmentProcedure[]> {
    const response = await this.client.get<TreatmentProcedure[]>(`/patients/${patientId}/procedures/upcoming`, {
      params: { days_ahead: daysAhead },
    });
    return response.data;
  }

  async getPatientCalendar(patientId: string, month: number, year: number): Promise<Record<string, TreatmentProcedure[]>> {
    const response = await this.client.get<Record<string, TreatmentProcedure[]>>(`/patients/${patientId}/procedures/calendar`, {
      params: { month, year },
    });
    return response.data;
  }

  async createProcedure(cycleId: string, procedure: TreatmentProcedureCreate): Promise<TreatmentProcedure> {
    const response = await this.client.post<TreatmentProcedure>(`/treatment-cycles/${cycleId}/procedures`, procedure);
    return response.data;
  }

  async updateProcedure(procedureId: string, update: TreatmentProcedureUpdate): Promise<TreatmentProcedure> {
    const response = await this.client.patch<TreatmentProcedure>(`/procedures/${procedureId}`, update);
    return response.data;
  }

  async completeProcedure(procedureId: string, details?: ProcedureComplete): Promise<TreatmentProcedure> {
    const response = await this.client.post<TreatmentProcedure>(`/procedures/${procedureId}/complete`, details || {});
    return response.data;
  }

  async cancelProcedure(procedureId: string, cancel?: ProcedureCancel): Promise<TreatmentProcedure> {
    const response = await this.client.post<TreatmentProcedure>(`/procedures/${procedureId}/cancel`, cancel || {});
    return response.data;
  }

  async deleteProcedure(procedureId: string): Promise<void> {
    await this.client.delete(`/procedures/${procedureId}`);
  }

  async generateProcedures(cycleId: string, data: {
    schedule_days: number[];
    procedure_type?: string;
    start_time?: string;
    location?: string;
  }): Promise<TreatmentProcedure[]> {
    const response = await this.client.post<TreatmentProcedure[]>(`/treatment-cycles/${cycleId}/procedures/generate`, data);
    return response.data;
  }

  // Test Data Management
  async populateTestData(): Promise<{
    success: boolean;
    message: string;
    patients_created: number;
    patient_ids: string[];
  }> {
    const response = await this.client.post('/patients/populate-test-data');
    return response.data;
  }

  async clearTestData(): Promise<{ success: boolean; patients_deleted: number }> {
    const response = await this.client.delete('/patients/clear-test-data');
    return response.data;
  }

  // Genomics
  async getGenomicReport(patientId: string): Promise<{
    report: GenomicReport;
    has_actionable_mutations: boolean;
    actionable_mutation_count: number;
  }> {
    const response = await this.client.get(`/patients/${patientId}/genomics`);
    return response.data;
  }

  async getPatientMutations(patientId: string, actionableOnly?: boolean): Promise<{
    patient_id: string;
    total_mutations: number;
    mutations: GenomicReport['mutations'];
  }> {
    const response = await this.client.get(`/patients/${patientId}/genomics/mutations`, {
      params: { actionable_only: actionableOnly },
    });
    return response.data;
  }

  async getPatientTargetedTherapies(patientId: string): Promise<{
    patient_id: string;
    total_therapies: number;
    therapies: Array<{
      drug: string;
      evidence_level: string;
      response_rate: number;
      indication: string;
      target_mutation: string;
    }>;
  }> {
    const response = await this.client.get(`/patients/${patientId}/genomics/therapies`);
    return response.data;
  }

  // Evidence
  async getPatientEvidence(patientId: string): Promise<{
    patient_id: string;
    publications: Array<{
      pmid: string;
      title: string;
      abstract: string;
      authors: string[];
      journal: string;
      publication_date: string;
      url: string;
      relevance: string;
    }>;
    guidelines: Array<{
      guideline: string;
      version: string;
      recommendation: string;
      evidence_level: string;
      applicable: boolean;
      notes: string;
    }>;
    evidence_summaries: Array<{
      treatment: string;
      evidence_strength: string;
      key_trials: Array<string | { name?: string; result?: string }>;
      guideline_recommendation?: string;
      guideline_recommendations?: Array<{ guideline?: string; source?: string; recommendation?: string; evidence_level?: string }>;
      summary: string;
      applicability_to_patient?: string;
    }>;
    search_terms: string[];
    recent_updates: string[];
  }> {
    const response = await this.client.get(`/patients/${patientId}/evidence`);
    return response.data;
  }

  async searchEvidence(params: {
    query: string;
    cancer_type?: string;
    biomarker?: string;
    drug?: string;
    max_results?: number;
  }): Promise<{
    query: string;
    total_results: number;
    publications: Array<{
      pmid: string;
      title: string;
      abstract: string;
      authors: string[];
      journal: string;
      publication_date: string;
      url: string;
    }>;
  }> {
    const response = await this.client.get('/evidence/search', { params });
    return response.data;
  }

  async getGuidelines(cancerType: string, biomarker?: string): Promise<{
    cancer_type: string;
    biomarker: string | null;
    total_guidelines: number;
    guidelines: Array<{
      guideline: string;
      version: string;
      recommendation: string;
      evidence_level: string;
      applicable: boolean;
      notes: string;
    }>;
  }> {
    const response = await this.client.get('/evidence/guidelines', {
      params: { cancer_type: cancerType, biomarker },
    });
    return response.data;
  }

  // Clinical Trials
  async getMatchedTrials(patientId: string, params?: {
    phase?: string;
    status?: string;
    min_match_score?: number;
  }): Promise<{ matched_trials: ClinicalTrial[]; total_trials_searched: number }> {
    // Backend endpoint: /api/v1/patients/{patient_id}/trials
    const response = await this.client.get(`/patients/${patientId}/trials`, { params });
    // Backend returns {trials: [...], matched_trials: count} - transform to expected format
    return {
      matched_trials: response.data.trials || [],
      total_trials_searched: response.data.total_trials_searched || 0
    };
  }

  async getTrialDetails(nctId: string): Promise<ClinicalTrial> {
    // Backend endpoint: /api/v1/trials/{nct_id}
    const response = await this.client.get<{ trial: ClinicalTrial }>(`/trials/${nctId}`);
    return response.data.trial;
  }

  async searchTrials(params: {
    condition?: string;
    intervention?: string;
    phase?: string;
    status?: string;
    limit?: number;
  }): Promise<{ total_results: number; trials: ClinicalTrial[] }> {
    // Backend endpoint: /api/v1/trials
    const response = await this.client.get('/trials', { params });
    return response.data;
  }

  // Treatment
  async getTreatmentPlan(patientId: string): Promise<TreatmentPlanResponse> {
    const response = await this.client.get<TreatmentPlanResponse>(`/patients/${patientId}/treatment`);
    return response.data;
  }

  async getTreatmentOptions(patientId: string): Promise<{ treatment_options: TreatmentPlan['treatment_options'] }> {
    const response = await this.client.get(`/patients/${patientId}/treatment/options`);
    return response.data;
  }

  // Analysis
  async getAnalysisStats(): Promise<{
    active_analyses: number;
    completed_today: number;
    clinical_notes_count: number;
    active_list: Array<{
      request_id: string;
      patient_id: string;
      status: string;
      progress_percent: number;
      current_step: string;
    }>;
  }> {
    const response = await this.client.get('/analysis/stats');
    return response.data;
  }

  async startAnalysis(request: AnalysisRequest): Promise<{ request_id: string }> {
    const response = await this.client.post<{ request_id: string }>('/analysis/run', request);
    return response.data;
  }

  async getAnalysisStatus(requestId: string): Promise<AnalysisProgress> {
    const response = await this.client.get<AnalysisProgress>(`/analysis/${requestId}/status`);
    return response.data;
  }

  async getAnalysisResults(requestId: string): Promise<AnalysisResult> {
    const response = await this.client.get<AnalysisResult>(`/analysis/${requestId}/results`);
    return response.data;
  }

  async getPatientAnalysisHistory(patientId: string, limit?: number): Promise<{
    patient_id: string;
    total: number;
    analyses: Array<{
      id: number;
      analysis_type: string;
      status: string;
      summary: string;
      key_findings: string[];
      confidence_score: number | null;
      created_at: string | null;
      completed_at: string | null;
    }>;
  }> {
    const response = await this.client.get(`/analysis/patient/${patientId}/history`, {
      params: { limit },
    });
    return response.data;
  }

  async getActiveAnalysis(patientId: string): Promise<{
    request_id: string;
    patient_id: string;
    status: string;
    progress_percent: number;
    current_step: string;
    current_step_detail: string;
    steps_completed: string[];
    steps_remaining: string[];
  } | null> {
    const response = await this.client.get(`/analysis/patient/${patientId}/active`);
    return response.data;
  }

  async stopAnalysis(requestId: string): Promise<{ message: string; request_id: string }> {
    const response = await this.client.post(`/analysis/${requestId}/stop`);
    return response.data;
  }

  // Analysis streaming with EventSource
  streamAnalysis(
    requestId: string,
    onProgress: (progress: AnalysisProgress) => void,
    onComplete: (result: AnalysisResult) => void,
    onError: (error: Error) => void
  ): () => void {
    const eventSource = new EventSource(`${API_BASE_URL}/api/v1/analysis/${requestId}/stream`);

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.status === 'completed') {
        // Extract the actual result from the nested structure
        onComplete(data.result || data);
        eventSource.close();
      } else if (data.status === 'error') {
        onError(new Error(data.error_message || 'Analysis failed'));
        eventSource.close();
      } else {
        onProgress(data);
      }
    };

    eventSource.onerror = () => {
      onError(new Error('Connection lost'));
      eventSource.close();
    };

    return () => eventSource.close();
  }

  // Chat
  async sendChatMessage(patientId: string, message: string): Promise<ChatResponse> {
    const response = await this.client.post<ChatResponse>(`/chat/${patientId}/message`, { message });
    return response.data;
  }

  async getChatHistory(patientId: string, limit?: number): Promise<{ messages: Array<{ role: string; content: string; timestamp: string }> }> {
    const response = await this.client.get(`/chat/${patientId}/history`, {
      params: { limit },
    });
    return response.data;
  }

  async clearChatHistory(patientId: string): Promise<void> {
    await this.client.delete(`/chat/${patientId}/history`);
  }

  // Clinical Notes
  async getClinicalNotes(patientId: string, noteType?: string): Promise<ClinicalNotesResponse> {
    const response = await this.client.get<ClinicalNotesResponse>(`/patients/${patientId}/clinical-notes`, {
      params: { note_type: noteType },
    });
    return response.data;
  }

  async getClinicalNote(noteId: string): Promise<ClinicalNote> {
    const response = await this.client.get<ClinicalNote>(`/clinical-notes/${noteId}`);
    return response.data;
  }

  async createClinicalNote(patientId: string, note: ClinicalNoteCreate): Promise<ClinicalNote> {
    const response = await this.client.post<ClinicalNote>(`/patients/${patientId}/clinical-notes`, note);
    return response.data;
  }

  async deleteClinicalNote(patientId: string, noteId: string): Promise<void> {
    await this.client.delete(`/patients/${patientId}/clinical-notes/${noteId}`);
  }

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    const response = await this.client.get('/health');
    return response.data;
  }

  // Email Notifications
  async notifyPatientOpened(patientId: string, userEmail: string): Promise<{ success: boolean; message: string }> {
    const response = await this.client.post('/notifications/patient-opened', {
      patient_id: patientId,
      user_email: userEmail,
    });
    return response.data;
  }

  async notifyPatientClosed(patientId: string, userEmail: string): Promise<{ success: boolean; message: string }> {
    const response = await this.client.post('/notifications/patient-closed', {
      patient_id: patientId,
      user_email: userEmail,
    });
    return response.data;
  }
}

export const api = new ApiClient();
export default api;
