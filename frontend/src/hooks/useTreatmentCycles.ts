'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { TreatmentCycle, TreatmentCycleCreate, TreatmentCycleUpdate } from '@/types';
import { patientKeys } from './usePatients';

export const treatmentCycleKeys = {
  all: ['treatmentCycles'] as const,
  lists: () => [...treatmentCycleKeys.all, 'list'] as const,
  list: (patientId: string) => [...treatmentCycleKeys.lists(), patientId] as const,
  details: () => [...treatmentCycleKeys.all, 'detail'] as const,
  detail: (cycleId: string) => [...treatmentCycleKeys.details(), cycleId] as const,
};

export function useTreatmentCycles(patientId: string, status?: string, limit?: number) {
  return useQuery({
    queryKey: treatmentCycleKeys.list(patientId),
    queryFn: () => api.getTreatmentCycles(patientId, status, limit),
    enabled: !!patientId,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

export function useTreatmentCycle(cycleId: string) {
  return useQuery({
    queryKey: treatmentCycleKeys.detail(cycleId),
    queryFn: () => api.getTreatmentCycle(cycleId),
    enabled: !!cycleId,
    staleTime: 2 * 60 * 1000,
  });
}

export function useCreateTreatmentCycle() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ patientId, cycle }: { patientId: string; cycle: TreatmentCycleCreate }) =>
      api.createTreatmentCycle(patientId, cycle),
    onSuccess: (_, { patientId }) => {
      queryClient.invalidateQueries({ queryKey: treatmentCycleKeys.list(patientId) });
      queryClient.invalidateQueries({ queryKey: patientKeys.timeline(patientId) });
    },
  });
}

export function useUpdateTreatmentCycle() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ cycleId, update, patientId }: { cycleId: string; update: TreatmentCycleUpdate; patientId: string }) =>
      api.updateTreatmentCycle(cycleId, update),
    onSuccess: (_, { cycleId, patientId }) => {
      queryClient.invalidateQueries({ queryKey: treatmentCycleKeys.detail(cycleId) });
      queryClient.invalidateQueries({ queryKey: treatmentCycleKeys.list(patientId) });
      queryClient.invalidateQueries({ queryKey: patientKeys.timeline(patientId) });
    },
  });
}

export function useDeleteTreatmentCycle() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ cycleId, patientId }: { cycleId: string; patientId: string }) =>
      api.deleteTreatmentCycle(cycleId),
    onSuccess: (_, { patientId }) => {
      queryClient.invalidateQueries({ queryKey: treatmentCycleKeys.lists() });
      queryClient.invalidateQueries({ queryKey: patientKeys.timeline(patientId) });
    },
  });
}
