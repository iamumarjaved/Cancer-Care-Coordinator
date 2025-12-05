'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export const trialsKeys = {
  all: ['trials'] as const,
  matched: (patientId: string) => [...trialsKeys.all, 'matched', patientId] as const,
  detail: (nctId: string) => [...trialsKeys.all, 'detail', nctId] as const,
  search: (params: Record<string, unknown>) => [...trialsKeys.all, 'search', params] as const,
};

export function useMatchedTrials(
  patientId: string | null,
  params?: {
    phase?: string;
    status?: string;
    min_match_score?: number;
  }
) {
  return useQuery({
    queryKey: [...trialsKeys.matched(patientId || ''), params],
    queryFn: () => api.getMatchedTrials(patientId!, params),
    enabled: !!patientId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useTrialDetails(nctId: string) {
  return useQuery({
    queryKey: trialsKeys.detail(nctId),
    queryFn: () => api.getTrialDetails(nctId),
    enabled: !!nctId,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

export function useSearchTrials(params: {
  condition?: string;
  intervention?: string;
  phase?: string;
  status?: string;
  limit?: number;
}) {
  return useQuery({
    queryKey: trialsKeys.search(params),
    queryFn: () => api.searchTrials(params),
    enabled: !!(params.condition || params.intervention),
    staleTime: 5 * 60 * 1000,
  });
}
