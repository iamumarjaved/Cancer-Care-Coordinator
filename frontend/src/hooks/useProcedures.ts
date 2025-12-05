'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type {
  TreatmentProcedure,
  TreatmentProcedureCreate,
  TreatmentProcedureUpdate,
  ProcedureComplete,
  ProcedureCancel,
} from '@/types';
import { patientKeys } from './usePatients';
import { treatmentCycleKeys } from './useTreatmentCycles';

export const procedureKeys = {
  all: ['procedures'] as const,
  lists: () => [...procedureKeys.all, 'list'] as const,
  cycleList: (cycleId: string) => [...procedureKeys.lists(), 'cycle', cycleId] as const,
  patientList: (patientId: string) => [...procedureKeys.lists(), 'patient', patientId] as const,
  upcoming: (patientId: string) => [...procedureKeys.all, 'upcoming', patientId] as const,
  calendar: (patientId: string, month: number, year: number) =>
    [...procedureKeys.all, 'calendar', patientId, month, year] as const,
  details: () => [...procedureKeys.all, 'detail'] as const,
  detail: (procedureId: string) => [...procedureKeys.details(), procedureId] as const,
};

// Get procedures for a specific treatment cycle
export function useProcedures(cycleId: string, status?: string, limit?: number) {
  return useQuery({
    queryKey: procedureKeys.cycleList(cycleId),
    queryFn: () => api.getProcedures(cycleId, status, limit),
    enabled: !!cycleId,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

// Get a single procedure
export function useProcedure(procedureId: string) {
  return useQuery({
    queryKey: procedureKeys.detail(procedureId),
    queryFn: () => api.getProcedure(procedureId),
    enabled: !!procedureId,
    staleTime: 2 * 60 * 1000,
  });
}

// Get all procedures for a patient
export function usePatientProcedures(
  patientId: string,
  params?: { status?: string; procedure_type?: string; limit?: number }
) {
  return useQuery({
    queryKey: procedureKeys.patientList(patientId),
    queryFn: () => api.getPatientProcedures(patientId, params),
    enabled: !!patientId,
    staleTime: 2 * 60 * 1000,
  });
}

// Get upcoming procedures for a patient
export function useUpcomingProcedures(patientId: string, daysAhead?: number) {
  return useQuery({
    queryKey: procedureKeys.upcoming(patientId),
    queryFn: () => api.getUpcomingProcedures(patientId, daysAhead),
    enabled: !!patientId,
    staleTime: 1 * 60 * 1000, // 1 minute - refresh more often for upcoming
  });
}

// Get patient calendar
export function usePatientCalendar(patientId: string, month: number, year: number) {
  return useQuery({
    queryKey: procedureKeys.calendar(patientId, month, year),
    queryFn: () => api.getPatientCalendar(patientId, month, year),
    enabled: !!patientId && month >= 1 && month <= 12 && year >= 2020,
    staleTime: 2 * 60 * 1000,
  });
}

// Create a new procedure
export function useCreateProcedure() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      cycleId,
      procedure,
      patientId,
    }: {
      cycleId: string;
      procedure: TreatmentProcedureCreate;
      patientId: string;
    }) => api.createProcedure(cycleId, procedure),
    onSuccess: (_, { cycleId, patientId }) => {
      queryClient.invalidateQueries({ queryKey: procedureKeys.cycleList(cycleId) });
      queryClient.invalidateQueries({ queryKey: procedureKeys.patientList(patientId) });
      queryClient.invalidateQueries({ queryKey: procedureKeys.upcoming(patientId) });
      // Invalidate calendar for current month
      const now = new Date();
      queryClient.invalidateQueries({
        queryKey: procedureKeys.calendar(patientId, now.getMonth() + 1, now.getFullYear()),
      });
    },
  });
}

// Update a procedure
export function useUpdateProcedure() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      procedureId,
      update,
      cycleId,
      patientId,
    }: {
      procedureId: string;
      update: TreatmentProcedureUpdate;
      cycleId: string;
      patientId: string;
    }) => api.updateProcedure(procedureId, update),
    onSuccess: (_, { procedureId, cycleId, patientId }) => {
      queryClient.invalidateQueries({ queryKey: procedureKeys.detail(procedureId) });
      queryClient.invalidateQueries({ queryKey: procedureKeys.cycleList(cycleId) });
      queryClient.invalidateQueries({ queryKey: procedureKeys.patientList(patientId) });
      queryClient.invalidateQueries({ queryKey: procedureKeys.upcoming(patientId) });
    },
  });
}

// Complete a procedure
export function useCompleteProcedure() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      procedureId,
      details,
      cycleId,
      patientId,
    }: {
      procedureId: string;
      details?: ProcedureComplete;
      cycleId: string;
      patientId: string;
    }) => api.completeProcedure(procedureId, details),
    onSuccess: (_, { procedureId, cycleId, patientId }) => {
      queryClient.invalidateQueries({ queryKey: procedureKeys.detail(procedureId) });
      queryClient.invalidateQueries({ queryKey: procedureKeys.cycleList(cycleId) });
      queryClient.invalidateQueries({ queryKey: procedureKeys.patientList(patientId) });
      queryClient.invalidateQueries({ queryKey: procedureKeys.upcoming(patientId) });
      queryClient.invalidateQueries({ queryKey: patientKeys.timeline(patientId) });
    },
  });
}

// Cancel a procedure
export function useCancelProcedure() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      procedureId,
      cancel,
      cycleId,
      patientId,
    }: {
      procedureId: string;
      cancel?: ProcedureCancel;
      cycleId: string;
      patientId: string;
    }) => api.cancelProcedure(procedureId, cancel),
    onSuccess: (_, { procedureId, cycleId, patientId }) => {
      queryClient.invalidateQueries({ queryKey: procedureKeys.detail(procedureId) });
      queryClient.invalidateQueries({ queryKey: procedureKeys.cycleList(cycleId) });
      queryClient.invalidateQueries({ queryKey: procedureKeys.patientList(patientId) });
      queryClient.invalidateQueries({ queryKey: procedureKeys.upcoming(patientId) });
    },
  });
}

// Delete a procedure
export function useDeleteProcedure() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      procedureId,
      cycleId,
      patientId,
    }: {
      procedureId: string;
      cycleId: string;
      patientId: string;
    }) => api.deleteProcedure(procedureId),
    onSuccess: (_, { cycleId, patientId }) => {
      queryClient.invalidateQueries({ queryKey: procedureKeys.lists() });
      queryClient.invalidateQueries({ queryKey: procedureKeys.upcoming(patientId) });
      queryClient.invalidateQueries({ queryKey: procedureKeys.patientList(patientId) });
    },
  });
}

// Generate procedures from schedule
export function useGenerateProcedures() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      cycleId,
      patientId,
      params,
    }: {
      cycleId: string;
      patientId: string;
      params: {
        schedule_days: number[];
        procedure_type?: string;
        start_time?: string;
        location?: string;
      };
    }) => api.generateProcedures(cycleId, params),
    onSuccess: (_, { cycleId, patientId }) => {
      queryClient.invalidateQueries({ queryKey: procedureKeys.cycleList(cycleId) });
      queryClient.invalidateQueries({ queryKey: procedureKeys.patientList(patientId) });
      queryClient.invalidateQueries({ queryKey: procedureKeys.upcoming(patientId) });
      // Invalidate calendar for current month
      const now = new Date();
      queryClient.invalidateQueries({
        queryKey: procedureKeys.calendar(patientId, now.getMonth() + 1, now.getFullYear()),
      });
    },
  });
}
