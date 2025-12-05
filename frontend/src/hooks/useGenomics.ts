'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export const genomicsKeys = {
  all: ['genomics'] as const,
  reports: () => [...genomicsKeys.all, 'report'] as const,
  report: (patientId: string) => [...genomicsKeys.reports(), patientId] as const,
  mutations: (patientId: string) => [...genomicsKeys.all, 'mutations', patientId] as const,
  therapies: (patientId: string) => [...genomicsKeys.all, 'therapies', patientId] as const,
};

export function useGenomicReport(patientId: string | null) {
  return useQuery({
    queryKey: genomicsKeys.report(patientId || ''),
    queryFn: () => api.getGenomicReport(patientId!),
    enabled: !!patientId,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

export function usePatientMutations(patientId: string | null, actionableOnly?: boolean) {
  return useQuery({
    queryKey: [...genomicsKeys.mutations(patientId || ''), actionableOnly],
    queryFn: () => api.getPatientMutations(patientId!, actionableOnly),
    enabled: !!patientId,
    staleTime: 10 * 60 * 1000,
  });
}

export function usePatientTargetedTherapies(patientId: string | null) {
  return useQuery({
    queryKey: genomicsKeys.therapies(patientId || ''),
    queryFn: () => api.getPatientTargetedTherapies(patientId!),
    enabled: !!patientId,
    staleTime: 10 * 60 * 1000,
  });
}
