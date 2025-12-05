'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export const evidenceKeys = {
  all: ['evidence'] as const,
  patient: (patientId: string) => [...evidenceKeys.all, 'patient', patientId] as const,
  search: (params: Record<string, unknown>) => [...evidenceKeys.all, 'search', params] as const,
  guidelines: (cancerType: string, biomarker?: string) =>
    [...evidenceKeys.all, 'guidelines', cancerType, biomarker] as const,
};

export function usePatientEvidence(patientId: string | null) {
  return useQuery({
    queryKey: evidenceKeys.patient(patientId || ''),
    queryFn: () => api.getPatientEvidence(patientId!),
    enabled: !!patientId,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

export function useSearchEvidence(params: {
  query: string;
  cancer_type?: string;
  biomarker?: string;
  drug?: string;
  max_results?: number;
}) {
  return useQuery({
    queryKey: evidenceKeys.search(params),
    queryFn: () => api.searchEvidence(params),
    enabled: !!params.query,
    staleTime: 10 * 60 * 1000,
  });
}

export function useGuidelines(cancerType: string, biomarker?: string) {
  return useQuery({
    queryKey: evidenceKeys.guidelines(cancerType, biomarker),
    queryFn: () => api.getGuidelines(cancerType, biomarker),
    enabled: !!cancerType,
    staleTime: 30 * 60 * 1000, // 30 minutes - guidelines don't change often
  });
}
