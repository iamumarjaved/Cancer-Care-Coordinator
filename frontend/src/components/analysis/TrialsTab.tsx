'use client';

import { useMatchedTrials, useAnalysisHistory } from '@/hooks';
import { Card, CardContent, CardHeader, CardTitle, Badge, Button } from '@/components/ui';
import { FlaskConical, MapPin, Calendar, ExternalLink, AlertCircle, CheckCircle, XCircle, HelpCircle } from 'lucide-react';
import { RunAnalysisPrompt } from './RunAnalysisPrompt';

interface TrialsTabProps {
  patientId: string;
}

export function TrialsTab({ patientId }: TrialsTabProps) {
  const { data: analysisHistory, isLoading: historyLoading } = useAnalysisHistory(patientId);
  const hasCompletedAnalysis = analysisHistory && analysisHistory.analyses.some(a => a.status === 'completed');

  // Only fetch trials data if analysis has been completed
  const { data, isLoading, error } = useMatchedTrials(hasCompletedAnalysis ? patientId : null);

  if (historyLoading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-32 bg-gray-200 rounded-lg" />
        <div className="h-32 bg-gray-200 rounded-lg" />
      </div>
    );
  }

  // Show prompt if no analysis has been completed
  if (!hasCompletedAnalysis) {
    return (
      <RunAnalysisPrompt
        patientId={patientId}
        tabName="Clinical Trials"
        description="Run an AI analysis to find clinical trials that match this patient's cancer type, mutations, and eligibility criteria."
        icon="trials"
      />
    );
  }

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-32 bg-gray-200 rounded-lg" />
        <div className="h-32 bg-gray-200 rounded-lg" />
        <div className="h-32 bg-gray-200 rounded-lg" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <AlertCircle className="w-10 h-10 mx-auto text-gray-300 mb-3" />
          <p className="text-gray-500">Clinical trials data not available</p>
        </CardContent>
      </Card>
    );
  }

  const { matched_trials: trials, total_trials_searched } = data;

  return (
    <div className="space-y-6">
      {/* Summary */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FlaskConical className="w-5 h-5 text-primary-600" />
              <CardTitle>Matched Clinical Trials</CardTitle>
            </div>
            <div className="text-sm text-gray-500">
              {trials.length} matches from {total_trials_searched.toLocaleString()} trials
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Trials List */}
      {trials.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <FlaskConical className="w-10 h-10 mx-auto text-gray-300 mb-3" />
            <p className="text-gray-500">No matching clinical trials found</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {trials.map((trial) => (
            <Card key={trial.nct_id} className="hover:border-primary-300 transition-colors">
              <CardContent className="p-6">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant="info">{trial.nct_id}</Badge>
                      <Badge
                        variant={
                          trial.phase === 'Phase 3' || trial.phase === 'PHASE3'
                            ? 'success'
                            : trial.phase === 'Phase 2' || trial.phase === 'PHASE2'
                            ? 'warning'
                            : 'info'
                        }
                      >
                        {trial.phase}
                      </Badge>
                      <Badge variant={trial.status === 'Recruiting' ? 'success' : 'info'}>
                        {trial.status}
                      </Badge>
                    </div>
                    <h3 className="font-semibold text-gray-900 mb-2">{trial.title}</h3>
                    {trial.brief_summary && (
                      <p className="text-sm text-gray-600 line-clamp-2 mb-3">
                        {trial.brief_summary}
                      </p>
                    )}

                    {/* Sponsor */}
                    {trial.sponsor && (
                      <p className="text-sm text-gray-500 mb-2">
                        <span className="font-medium">Sponsor:</span> {trial.sponsor}
                      </p>
                    )}

                    {/* Interventions */}
                    {trial.interventions && trial.interventions.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-3">
                        {trial.interventions.map((intervention, i) => (
                          <Badge key={i} variant="info" className="text-xs">
                            {intervention}
                          </Badge>
                        ))}
                      </div>
                    )}

                    {/* Eligibility Criteria */}
                    {trial.eligibility_criteria && trial.eligibility_criteria.length > 0 && (
                      <div className="mb-3">
                        <p className="text-sm font-medium text-gray-700 mb-2">Eligibility Check:</p>
                        <div className="grid gap-1">
                          {trial.eligibility_criteria.slice(0, 4).map((criterion, i) => (
                            <div key={i} className="flex items-center gap-2 text-sm">
                              {criterion.patient_meets === true ? (
                                <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                              ) : criterion.patient_meets === false ? (
                                <XCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
                              ) : (
                                <HelpCircle className="w-4 h-4 text-yellow-500 flex-shrink-0" />
                              )}
                              <span className="text-gray-600">{criterion.criterion}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Locations */}
                    {trial.locations && trial.locations.length > 0 && (
                      <div className="flex items-center gap-2 text-sm text-gray-500">
                        <MapPin className="w-4 h-4" />
                        <span>
                          {trial.locations.slice(0, 2).join(', ')}
                          {trial.locations.length > 2 && ` +${trial.locations.length - 2} more`}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Match Score */}
                  <div className="text-right flex-shrink-0">
                    <div
                      className={`text-3xl font-bold ${
                        trial.match_score >= 0.8
                          ? 'text-green-600'
                          : trial.match_score >= 0.6
                          ? 'text-yellow-600'
                          : 'text-gray-600'
                      }`}
                    >
                      {Math.round(trial.match_score * 100)}%
                    </div>
                    <p className="text-xs text-gray-500">Match Score</p>
                    <a
                      href={`https://clinicaltrials.gov/study/${trial.nct_id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-2 inline-flex items-center gap-1 text-sm text-primary-600 hover:text-primary-700"
                    >
                      View on CT.gov
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                </div>

                {/* Rationale */}
                {trial.match_rationale && (
                  <div className="mt-4 p-3 bg-green-50 rounded-lg border border-green-100">
                    <p className="text-sm text-green-800">
                      <span className="font-medium">Match Rationale:</span> {trial.match_rationale}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
