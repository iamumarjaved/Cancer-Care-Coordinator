'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { ClinicalNote, ClinicalNoteCreate, ClinicalNotesResponse } from '@/types';

export const clinicalNoteKeys = {
  all: ['clinicalNotes'] as const,
  lists: () => [...clinicalNoteKeys.all, 'list'] as const,
  patientList: (patientId: string) => [...clinicalNoteKeys.lists(), 'patient', patientId] as const,
  details: () => [...clinicalNoteKeys.all, 'detail'] as const,
  detail: (noteId: string) => [...clinicalNoteKeys.details(), noteId] as const,
};

// Get all clinical notes for a patient
export function useClinicalNotes(patientId: string | null, noteType?: string) {
  return useQuery({
    queryKey: clinicalNoteKeys.patientList(patientId || ''),
    queryFn: () => api.getClinicalNotes(patientId!, noteType),
    enabled: !!patientId,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

// Get a single clinical note
export function useClinicalNote(noteId: string) {
  return useQuery({
    queryKey: clinicalNoteKeys.detail(noteId),
    queryFn: () => api.getClinicalNote(noteId),
    enabled: !!noteId,
    staleTime: 2 * 60 * 1000,
  });
}

// Create a new clinical note
export function useCreateClinicalNote() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      patientId,
      note,
    }: {
      patientId: string;
      note: ClinicalNoteCreate;
    }) => api.createClinicalNote(patientId, note),
    onSuccess: (_, { patientId }) => {
      queryClient.invalidateQueries({ queryKey: clinicalNoteKeys.patientList(patientId) });
    },
  });
}

// Delete a clinical note
export function useDeleteClinicalNote() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      patientId,
      noteId,
    }: {
      patientId: string;
      noteId: string;
    }) => api.deleteClinicalNote(patientId, noteId),
    onSuccess: (_, { patientId }) => {
      queryClient.invalidateQueries({ queryKey: clinicalNoteKeys.patientList(patientId) });
    },
  });
}
