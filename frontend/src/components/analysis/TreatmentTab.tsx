'use client';

import { useTreatmentPlan, useAnalysisHistory, useMatchedTrials } from '@/hooks';
import { Card, CardContent, CardHeader, CardTitle, Badge, Button } from '@/components/ui';
import { Pill, Star, AlertTriangle, CheckCircle, MessageSquare, AlertCircle } from 'lucide-react';
import { RunAnalysisPrompt } from './RunAnalysisPrompt';

interface TreatmentTabProps {
  patientId: string;
}

// Helper to get confidence score from either field name
function getConfidenceScore(option: { confidence_score?: number; confidence?: number }): number {
  return option.confidence_score ?? option.confidence ?? 0;
}

// Helper to clean up summary text (remove "Unknown" patterns and fix trial count)
function cleanSummary(summary: string, actualTrialCount?: number): string {
  let cleaned = summary
    .replace(/Unknown year old\s*/gi, '')
    .replace(/Patient:\s+with/gi, 'Patient with')
    .replace(/\s+,/g, ',')
    .replace(/,\s*,/g, ',')
    .trim();

  // If we have actual trial count, replace the AI-generated count with the real one
  if (actualTrialCount !== undefined) {
    cleaned = cleaned.replace(
      /\d+ clinical trials? identified/gi,
      `${actualTrialCount} clinical trial${actualTrialCount !== 1 ? 's' : ''} identified`
    );
  }

  return cleaned;
}

export function TreatmentTab({ patientId }: TreatmentTabProps) {
  const { data: analysisHistory, isLoading: historyLoading } = useAnalysisHistory(patientId);
  const hasCompletedAnalysis = analysisHistory && analysisHistory.analyses.some(a => a.status === 'completed');

  // Only fetch treatment data if analysis has been completed
  const { data, isLoading, error } = useTreatmentPlan(hasCompletedAnalysis ? patientId : null);

  // Also fetch trials to get the actual count (fixes inconsistency with Trials tab)
  const { data: trialsData } = useMatchedTrials(hasCompletedAnalysis ? patientId : null);
  const actualTrialCount = trialsData?.matched_trials?.length;

  if (historyLoading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-48 bg-gray-200 rounded-lg" />
        <div className="h-32 bg-gray-200 rounded-lg" />
      </div>
    );
  }

  // Show prompt if no analysis has been completed
  if (!hasCompletedAnalysis) {
    return (
      <RunAnalysisPrompt
        patientId={patientId}
        tabName="Treatment Recommendations"
        description="Run an AI analysis to generate personalized treatment recommendations based on the patient's cancer type, genomic profile, and clinical guidelines."
        icon="treatment"
      />
    );
  }

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-48 bg-gray-200 rounded-lg" />
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
          <p className="text-gray-500">Treatment plan not available</p>
        </CardContent>
      </Card>
    );
  }

  const { plan, requires_approval } = data;

  return (
    <div className="space-y-6">
      {/* Summary */}
      {plan.summary && (
        <Card className="border-primary-200 bg-primary-50/30">
          <CardContent className="p-6">
            <p className="text-gray-800">{cleanSummary(plan.summary, actualTrialCount)}</p>
          </CardContent>
        </Card>
      )}

      {/* Primary Recommendation */}
      {plan.primary_recommendation && (
        <Card className="border-green-200">
          <CardHeader className="bg-green-50/50">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Star className="w-5 h-5 text-green-600" />
                <CardTitle className="text-green-800">Primary Recommendation</CardTitle>
              </div>
              {getConfidenceScore(plan.primary_recommendation) > 0 && (
                <Badge variant="success">
                  {Math.round(getConfidenceScore(plan.primary_recommendation) * 100)}% Confidence
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent className="p-6">
            <TreatmentOptionCard option={plan.primary_recommendation} isPrimary />
          </CardContent>
        </Card>
      )}

      {/* Alternative Options */}
      {plan.alternative_options && plan.alternative_options.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Pill className="w-5 h-5 text-primary-600" />
              <CardTitle>Alternative Treatment Options</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {plan.alternative_options.map((option, i) => (
                <div key={i} className="p-4 border border-gray-200 rounded-lg">
                  <TreatmentOptionCard option={option} />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Discussion Points */}
      {plan.discussion_points && plan.discussion_points.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-primary-600" />
              <CardTitle>Discussion Points with Patient</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <ul className="space-y-3">
              {plan.discussion_points.map((point, i) => (
                <li key={i} className="flex items-start gap-3">
                  <span className="w-6 h-6 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-sm font-medium flex-shrink-0">
                    {i + 1}
                  </span>
                  <span className="text-gray-700">{point}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Approval Status */}
      {requires_approval && (
        <Card className="border-yellow-200 bg-yellow-50/30">
          <CardContent className="p-6">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-6 h-6 text-yellow-600" />
              <div>
                <p className="font-medium text-yellow-800">Pending Review</p>
                <p className="text-sm text-yellow-700">
                  This treatment plan requires physician approval before implementation.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

interface TreatmentOptionCardProps {
  option: {
    name: string;
    category?: string;
    description?: string;
    dosing?: string;
    recommendation_level?: string;
    confidence_score?: number;
    evidence_level?: string;
    expected_outcomes?: Record<string, unknown>;
    supporting_evidence?: string[];
    contraindications?: string[];
    patient_specific_considerations?: string[];
    rationale?: string;
  };
  isPrimary?: boolean;
}

function TreatmentOptionCard({ option, isPrimary }: TreatmentOptionCardProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between">
        <div>
          <h3 className={`font-semibold ${isPrimary ? 'text-xl' : 'text-lg'} text-gray-900`}>
            {option.name}
          </h3>
          {option.category && (
            <Badge variant="info" className="mt-1">
              {option.category}
            </Badge>
          )}
        </div>
        {option.evidence_level && (
          <Badge variant="success">{option.evidence_level}</Badge>
        )}
      </div>

      {option.description && <p className="text-gray-600">{option.description}</p>}

      {option.dosing && (
        <div className="p-3 bg-gray-50 rounded-lg">
          <p className="text-sm">
            <span className="font-medium text-gray-700">Dosing:</span> {option.dosing}
          </p>
        </div>
      )}

      {option.expected_outcomes && Object.keys(option.expected_outcomes).length > 0 && (
        <div>
          <p className="text-sm font-medium text-gray-700 mb-2">Expected Outcomes:</p>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {Object.entries(option.expected_outcomes).map(([key, value]) => (
              <div key={key} className="p-3 bg-green-50 rounded-lg text-center">
                <p className="text-xs text-gray-500">{key.replace(/_/g, ' ')}</p>
                <p className="font-semibold text-green-700">
                  {typeof value === 'number'
                    ? value <= 1
                      ? `${Math.round(value * 100)}%`  // Decimal (0.37) → 37%
                      : value <= 100
                        ? `${Math.round(value)}%`     // Already percentage (37.1) → 37%
                        : String(value)               // Large numbers (days, etc.)
                    : typeof value === 'string'
                      ? value
                      : value === null || value === undefined
                        ? 'N/A'
                        : String(value)}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {option.supporting_evidence && option.supporting_evidence.length > 0 && (
        <div>
          <p className="text-sm font-medium text-gray-700 mb-2">Supporting Evidence:</p>
          <ul className="text-sm text-gray-600 space-y-1">
            {option.supporting_evidence.map((evidence, i) => (
              <li key={i} className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                {evidence}
              </li>
            ))}
          </ul>
        </div>
      )}

      {option.patient_specific_considerations &&
        option.patient_specific_considerations.length > 0 && (
          <div>
            <p className="text-sm font-medium text-gray-700 mb-2">Patient-Specific Considerations:</p>
            <ul className="text-sm text-gray-600 space-y-1">
              {option.patient_specific_considerations.map((consideration, i) => (
                <li key={i} className="flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                  {consideration}
                </li>
              ))}
            </ul>
          </div>
        )}

      {option.contraindications && option.contraindications.length > 0 && (
        <div className="p-3 bg-red-50 rounded-lg">
          <p className="text-sm font-medium text-red-700 mb-1">Contraindications:</p>
          <ul className="text-sm text-red-600 space-y-1">
            {option.contraindications.map((contraindication, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-red-400">•</span>
                {contraindication}
              </li>
            ))}
          </ul>
        </div>
      )}

      {option.rationale && (
        <div className="p-3 bg-primary-50 rounded-lg border border-primary-100">
          <p className="text-sm text-primary-800">
            <span className="font-medium">Rationale:</span> {option.rationale}
          </p>
        </div>
      )}
    </div>
  );
}
