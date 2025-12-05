'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { TreatmentPlanResponse } from '@/types';

export const treatmentKeys = {
  all: ['treatment'] as const,
  plans: () => [...treatmentKeys.all, 'plan'] as const,
  plan: (patientId: string) => [...treatmentKeys.plans(), patientId] as const,
  options: (patientId: string) => [...treatmentKeys.all, 'options', patientId] as const,
};

export function useTreatmentPlan(patientId: string | null) {
  return useQuery<TreatmentPlanResponse>({
    queryKey: treatmentKeys.plan(patientId || ''),
    queryFn: () => api.getTreatmentPlan(patientId!),
    enabled: !!patientId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useTreatmentOptions(patientId: string) {
  return useQuery({
    queryKey: treatmentKeys.options(patientId),
    queryFn: () => api.getTreatmentOptions(patientId),
    enabled: !!patientId,
    staleTime: 5 * 60 * 1000,
  });
}
