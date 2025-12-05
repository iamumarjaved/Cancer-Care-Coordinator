'use client';

import { AnalysisProgress as AnalysisProgressType } from '@/types';
import { Card, CardContent, CardHeader, CardTitle, Progress, Badge } from '@/components/ui';
import { CheckCircle, Circle, AlertCircle, Loader2 } from 'lucide-react';

interface AnalysisProgressProps {
  progress: AnalysisProgressType;
}

const stepLabels: Record<string, string> = {
  initializing: 'Loading Patient Data',
  data_collection: 'Collecting Patient Data',
  medical_history: 'Analyzing Medical History',
  genomics: 'Interpreting Genomics',
  genomics_analysis: 'Interpreting Genomics',  // Legacy support
  clinical_trials: 'Matching Clinical Trials',
  evidence: 'Searching Medical Literature',
  evidence_research: 'Searching Medical Literature',  // Legacy support
  treatment: 'Generating Treatment Options',
  treatment_synthesis: 'Generating Treatment Options',  // Legacy support
  synthesizing: 'Synthesizing Results',
  report_generation: 'Synthesizing Results',  // Legacy support
  completed: 'Analysis Complete',
  error: 'Error Occurred',
};

export function AnalysisProgressComponent({ progress }: AnalysisProgressProps) {
  const getStepIcon = (step: string) => {
    if (progress.steps_completed.includes(step) || progress.steps_completed.includes(`${step} (skipped)`)) {
      return <CheckCircle className="w-5 h-5 text-success-500" />;
    }
    if (progress.current_step === step) {
      return <Loader2 className="w-5 h-5 text-primary-500 animate-spin" />;
    }
    if (progress.status === 'error') {
      return <AlertCircle className="w-5 h-5 text-danger-500" />;
    }
    return <Circle className="w-5 h-5 text-secondary-300" />;
  };

  // Step names that match the backend orchestrator
  const allSteps = ['medical_history', 'genomics', 'clinical_trials', 'evidence', 'treatment', 'synthesizing'];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Analysis Progress</CardTitle>
          <Badge variant={progress.status === 'error' ? 'danger' : progress.status === 'completed' ? 'success' : 'info'}>
            {progress.status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Progress Bar */}
        <Progress
          value={progress.progress_percent}
          showValue
          label={progress.current_step_detail || stepLabels[progress.current_step]}
        />

        {/* Steps Timeline */}
        <div className="space-y-3">
          {allSteps.map((step, index) => (
            <div key={step} className="flex items-center gap-3">
              {getStepIcon(step)}
              <div className="flex-1">
                <p className={`text-sm font-medium ${
                  progress.current_step === step
                    ? 'text-primary-600'
                    : progress.steps_completed.includes(step)
                    ? 'text-secondary-700'
                    : 'text-secondary-400'
                }`}>
                  {stepLabels[step]}
                </p>
                {progress.current_step === step && progress.current_step_detail && (
                  <p className="text-xs text-secondary-500">{progress.current_step_detail}</p>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Error Message */}
        {progress.error_message && (
          <div className="p-3 bg-danger-50 border border-danger-200 rounded-md">
            <p className="text-sm text-danger-700">{progress.error_message}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
