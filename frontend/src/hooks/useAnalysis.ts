'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { AnalysisRequest, AnalysisProgress, AnalysisResult } from '@/types';

export const analysisKeys = {
  all: ['analysis'] as const,
  status: (requestId: string) => [...analysisKeys.all, 'status', requestId] as const,
  results: (requestId: string) => [...analysisKeys.all, 'results', requestId] as const,
  history: (patientId: string) => [...analysisKeys.all, 'history', patientId] as const,
};

export function useAnalysisStatus(requestId: string | null) {
  return useQuery({
    queryKey: analysisKeys.status(requestId || ''),
    queryFn: () => api.getAnalysisStatus(requestId!),
    enabled: !!requestId,
    refetchInterval: (query) => {
      // Poll every 2 seconds while in progress
      const data = query.state.data as AnalysisProgress | undefined;
      if (data?.status === 'completed' || data?.status === 'error') {
        return false;
      }
      return 2000;
    },
  });
}

export function useAnalysisResults(requestId: string | null) {
  return useQuery({
    queryKey: analysisKeys.results(requestId || ''),
    queryFn: () => api.getAnalysisResults(requestId!),
    enabled: !!requestId,
    staleTime: Infinity, // Results don't change
  });
}

export function useStartAnalysis() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: AnalysisRequest) => api.startAnalysis(request),
    onSuccess: (data) => {
      // Prefetch status
      queryClient.prefetchQuery({
        queryKey: analysisKeys.status(data.request_id),
        queryFn: () => api.getAnalysisStatus(data.request_id),
      });
    },
  });
}

export function useStreamingAnalysis() {
  const [progress, setProgress] = useState<AnalysisProgress | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const cleanupRef = useRef<(() => void) | null>(null);

  const startStreaming = useCallback((requestId: string) => {
    setIsStreaming(true);
    setProgress(null);
    setResult(null);
    setError(null);

    cleanupRef.current = api.streamAnalysis(
      requestId,
      (progressUpdate) => {
        setProgress(progressUpdate);
      },
      (analysisResult) => {
        setResult(analysisResult);
        setIsStreaming(false);
      },
      (err) => {
        setError(err);
        setIsStreaming(false);
      }
    );
  }, []);

  const stopStreaming = useCallback(() => {
    if (cleanupRef.current) {
      cleanupRef.current();
      cleanupRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (cleanupRef.current) {
        cleanupRef.current();
      }
    };
  }, []);

  return {
    progress,
    result,
    error,
    isStreaming,
    startStreaming,
    stopStreaming,
  };
}

export function useRunAnalysis(patientId: string) {
  const startAnalysis = useStartAnalysis();
  const streaming = useStreamingAnalysis();
  const queryClient = useQueryClient();

  const runAnalysis = useCallback(
    async (options?: {
      include_trials?: boolean;
      include_evidence?: boolean;
      user_questions?: string[];
      user_email?: string;
    }) => {
      try {
        const { request_id } = await startAnalysis.mutateAsync({
          patient_id: patientId,
          include_trials: options?.include_trials ?? true,
          include_evidence: options?.include_evidence ?? true,
          user_questions: options?.user_questions ?? [],
          user_email: options?.user_email,
        });

        streaming.startStreaming(request_id);
        return request_id;
      } catch (err) {
        throw err;
      }
    },
    [patientId, startAnalysis, streaming]
  );

  return {
    runAnalysis,
    progress: streaming.progress,
    result: streaming.result,
    error: streaming.error || startAnalysis.error,
    isLoading: startAnalysis.isPending || streaming.isStreaming,
  };
}

export function useAnalysisHistory(patientId: string | null) {
  return useQuery({
    queryKey: analysisKeys.history(patientId || ''),
    queryFn: () => api.getPatientAnalysisHistory(patientId!),
    enabled: !!patientId,
    staleTime: 60 * 1000, // 1 minute
  });
}

export function useActiveAnalysis(patientId: string | null) {
  return useQuery({
    queryKey: [...analysisKeys.all, 'active', patientId] as const,
    queryFn: () => api.getActiveAnalysis(patientId!),
    enabled: !!patientId,
    refetchInterval: 2000, // Poll every 2 seconds to detect new analyses
  });
}

export function useStopAnalysis() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (requestId: string) => api.stopAnalysis(requestId),
    onSuccess: () => {
      // Invalidate active analysis queries
      queryClient.invalidateQueries({ queryKey: analysisKeys.all });
    },
  });
}
