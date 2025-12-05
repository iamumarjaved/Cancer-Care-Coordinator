'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Patient, PatientSummary, PatientStatusUpdate, PatientEvent, PaginatedResponse } from '@/types';

export const patientKeys = {
  all: ['patients'] as const,
  lists: () => [...patientKeys.all, 'list'] as const,
  list: (filters: Record<string, unknown>) => [...patientKeys.lists(), filters] as const,
  details: () => [...patientKeys.all, 'detail'] as const,
  detail: (id: string) => [...patientKeys.details(), id] as const,
  summary: (id: string) => [...patientKeys.all, 'summary', id] as const,
  status: (id: string) => [...patientKeys.all, 'status', id] as const,
  timeline: (id: string) => [...patientKeys.all, 'timeline', id] as const,
};

export function usePatients(params?: {
  page?: number;
  page_size?: number;
  cancer_type?: string;
  search?: string;
}) {
  return useQuery({
    queryKey: patientKeys.list(params || {}),
    queryFn: () => api.getPatients(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function usePatient(patientId: string) {
  return useQuery({
    queryKey: patientKeys.detail(patientId),
    queryFn: () => api.getPatient(patientId),
    enabled: !!patientId,
    staleTime: 5 * 60 * 1000,
  });
}

export function usePatientSummary(patientId: string) {
  return useQuery({
    queryKey: patientKeys.summary(patientId),
    queryFn: () => api.getPatientSummary(patientId),
    enabled: !!patientId,
    staleTime: 5 * 60 * 1000,
  });
}

export function useCreatePatient() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (patient: Omit<Patient, 'id'>) => api.createPatient(patient),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: patientKeys.lists() });
    },
  });
}

export function useUpdatePatient() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, patient }: { id: string; patient: Partial<Patient> }) =>
      api.updatePatient(id, patient),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: patientKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: patientKeys.lists() });
    },
  });
}

export function useDeletePatient() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (patientId: string) => api.deletePatient(patientId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: patientKeys.lists() });
    },
  });
}

export function usePatientTimeline(patientId: string, limit?: number) {
  return useQuery({
    queryKey: patientKeys.timeline(patientId),
    queryFn: () => api.getPatientTimeline(patientId, limit),
    enabled: !!patientId,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

export function useUpdatePatientStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, statusUpdate }: { id: string; statusUpdate: PatientStatusUpdate }) =>
      api.updatePatientStatus(id, statusUpdate),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: patientKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: patientKeys.status(id) });
      queryClient.invalidateQueries({ queryKey: patientKeys.timeline(id) });
      queryClient.invalidateQueries({ queryKey: patientKeys.lists() });
    },
  });
}
