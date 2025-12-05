'use client';

import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { ChatRequest, ChatResponse } from '@/types';

export const chatKeys = {
  all: ['chat'] as const,
  history: (patientId: string) => [...chatKeys.all, 'history', patientId] as const,
};

interface ChatMessage {
  id: string;
  role: 'patient' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  suggestedFollowups?: string[];
  requiresEscalation?: boolean;
  escalationReason?: string;
}

export function useChatHistory(patientId: string, limit?: number) {
  return useQuery({
    queryKey: chatKeys.history(patientId),
    queryFn: () => api.getChatHistory(patientId, limit),
    enabled: !!patientId,
  });
}

export function useClearChatHistory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (patientId: string) => api.clearChatHistory(patientId),
    onSuccess: (_, patientId) => {
      queryClient.invalidateQueries({ queryKey: chatKeys.history(patientId) });
    },
  });
}

export function useChat(patientId: string) {
  const queryClient = useQueryClient();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const sendMessage = useMutation({
    mutationFn: (message: string) => api.sendChatMessage(patientId, message),
    onMutate: async (message) => {
      // Optimistically add user message
      const userMessage: ChatMessage = {
        id: `temp-${Date.now()}`,
        role: 'patient',
        content: message,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);
      setError(null);
    },
    onSuccess: (response) => {
      // Add assistant response
      const assistantMessage: ChatMessage = {
        id: `msg-${Date.now()}`,
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString(),
        suggestedFollowups: response.suggested_followup,
        requiresEscalation: response.escalate_to_human,
        escalationReason: response.escalation_reason,
      };
      setMessages((prev) => [...prev, assistantMessage]);

      // Invalidate chat history cache
      queryClient.invalidateQueries({ queryKey: chatKeys.history(patientId) });
    },
    onError: (err: Error) => {
      // Remove the optimistic message on error
      setMessages((prev) => prev.slice(0, -1));
      setError(err);
    },
    onSettled: () => {
      setIsLoading(false);
    },
  });

  const send = useCallback(
    async (message: string) => {
      await sendMessage.mutateAsync(message);
    },
    [sendMessage]
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  const loadHistory = useCallback(async () => {
    try {
      const { messages: history } = await api.getChatHistory(patientId);
      const loadedMessages: ChatMessage[] = history.map((msg, index) => ({
        id: `history-${index}`,
        role: msg.role as 'patient' | 'assistant' | 'system',
        content: msg.content,
        timestamp: msg.timestamp,
      }));
      setMessages(loadedMessages);
    } catch (err) {
      setError(err as Error);
    }
  }, [patientId]);

  return {
    messages,
    isLoading,
    error,
    send,
    clearMessages,
    loadHistory,
  };
}
