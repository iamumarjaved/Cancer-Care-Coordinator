'use client';

import { useState, useRef, useEffect } from 'react';
import { useChat } from '@/hooks/useChat';
import { Card, CardContent, CardHeader, CardTitle, Button, Badge } from '@/components/ui';
import { Send, User, Bot, AlertTriangle, RefreshCw } from 'lucide-react';
import { cn, formatRelativeTime } from '@/lib/utils';

interface ChatProps {
  patientId: string;
}

export function Chat({ patientId }: ChatProps) {
  const { messages, isLoading, error, send, clearMessages, loadHistory } = useChat(patientId);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const message = input.trim();
    setInput('');
    await send(message);
  };

  const handleSuggestedQuestion = (question: string) => {
    send(question);
  };

  return (
    <Card className="h-[calc(100vh-280px)] min-h-[500px] max-h-[800px] flex flex-col">
      <CardHeader className="pb-3 border-b flex-shrink-0">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Patient Chat</CardTitle>
          <Button variant="ghost" size="sm" onClick={clearMessages}>
            <RefreshCw className="w-4 h-4 mr-1" />
            Clear
          </Button>
        </div>
      </CardHeader>
      <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-secondary-500 py-8">
            <Bot className="w-12 h-12 mx-auto mb-2 text-secondary-300" />
            <p>Start a conversation about your treatment plan, test results, or any questions you have.</p>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={message.id || index}
            className={cn(
              'flex gap-3',
              message.role === 'patient' ? 'justify-end' : 'justify-start'
            )}
          >
            {message.role !== 'patient' && (
              <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0">
                <Bot className="w-4 h-4 text-primary-600" />
              </div>
            )}

            <div
              className={cn(
                'max-w-[80%] rounded-lg p-3',
                message.role === 'patient'
                  ? 'bg-primary-600 text-white'
                  : 'bg-secondary-100 text-secondary-900'
              )}
            >
              <p className="text-sm whitespace-pre-wrap">{message.content}</p>

              {/* Escalation Warning */}
              {message.requiresEscalation && (
                <div className="mt-2 p-2 bg-warning-50 rounded-md flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-warning-600 mt-0.5" />
                  <div>
                    <p className="text-xs font-medium text-warning-700">Escalation Required</p>
                    {message.escalationReason && (
                      <p className="text-xs text-warning-600">{message.escalationReason}</p>
                    )}
                  </div>
                </div>
              )}

              {/* Suggested Follow-ups */}
              {message.suggestedFollowups && message.suggestedFollowups.length > 0 && (
                <div className="mt-3 pt-2 border-t border-secondary-200">
                  <p className="text-xs text-secondary-500 mb-2">Suggested questions:</p>
                  <div className="flex flex-wrap gap-1">
                    {message.suggestedFollowups.map((question, i) => (
                      <button
                        key={i}
                        onClick={() => handleSuggestedQuestion(question)}
                        className="text-xs bg-white text-primary-600 px-2 py-1 rounded hover:bg-primary-50 transition-colors"
                      >
                        {question}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <p
                className={cn(
                  'text-xs mt-1',
                  message.role === 'patient' ? 'text-primary-200' : 'text-secondary-400'
                )}
              >
                {formatRelativeTime(message.timestamp)}
              </p>
            </div>

            {message.role === 'patient' && (
              <div className="w-8 h-8 rounded-full bg-secondary-200 flex items-center justify-center flex-shrink-0">
                <User className="w-4 h-4 text-secondary-600" />
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center">
              <Bot className="w-4 h-4 text-primary-600" />
            </div>
            <div className="bg-secondary-100 rounded-lg p-3">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-secondary-400 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-secondary-400 rounded-full animate-bounce delay-100" />
                <div className="w-2 h-2 bg-secondary-400 rounded-full animate-bounce delay-200" />
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="p-3 bg-danger-50 border border-danger-200 rounded-md">
            <p className="text-sm text-danger-700">{error.message}</p>
          </div>
        )}

        <div ref={messagesEndRef} />
      </CardContent>

      <div className="p-4 border-t flex-shrink-0 bg-white">
        <form onSubmit={handleSubmit} className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about your treatment..."
            className="flex-1 px-4 py-3 border border-secondary-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-base"
            disabled={isLoading}
          />
          <Button type="submit" disabled={!input.trim() || isLoading} className="px-6">
            <Send className="w-5 h-5" />
          </Button>
        </form>
      </div>
    </Card>
  );
}
