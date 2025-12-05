'use client';

import { AnalysisResult } from '@/types';
import { Card, CardContent, CardHeader, CardTitle, Badge } from '@/components/ui';
import { TreatmentCard } from '@/components/treatment/TreatmentCard';
import { ClinicalTrialCard } from '@/components/treatment/ClinicalTrialCard';
import { formatDateTime } from '@/lib/utils';
import { FileText, Lightbulb, AlertTriangle, Pill, TestTube } from 'lucide-react';

interface AnalysisResultsProps {
  result: AnalysisResult;
}

export function AnalysisResults({ result }: AnalysisResultsProps) {
  // Defensive checks for potentially undefined fields
  const keyFindings = result?.key_findings ?? [];
  const recommendations = result?.recommendations ?? [];
  const clinicalTrials = result?.clinical_trials ?? [];
  const sourcesUsed = result?.sources_used ?? [];

  if (!result) {
    return (
      <Card>
        <CardContent className="p-6 text-center">
          <p className="text-secondary-500">No analysis results available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-primary-600" />
            <CardTitle>Analysis Summary</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-secondary-700">{result.summary || 'Analysis complete.'}</p>
          {result.completed_at && (
            <p className="text-sm text-secondary-500 mt-2">
              Completed at {formatDateTime(result.completed_at)}
            </p>
          )}
        </CardContent>
      </Card>

      {/* Key Findings */}
      {keyFindings.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Lightbulb className="w-5 h-5 text-warning-500" />
              <CardTitle>Key Findings</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {keyFindings.map((finding, index) => (
                <li key={index} className="flex items-start gap-2">
                  <span className="w-6 h-6 rounded-full bg-warning-100 text-warning-600 flex items-center justify-center text-xs font-medium">
                    {index + 1}
                  </span>
                  <span className="text-secondary-700">{finding}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-primary-600" />
              <CardTitle>Recommendations</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {recommendations.map((rec, index) => (
                <li key={index} className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-primary-500 mt-2" />
                  <span className="text-secondary-700">{rec}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Treatment Plan */}
      {result.treatment_plan && result.treatment_plan.treatment_options?.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-4">
            <Pill className="w-5 h-5 text-primary-600" />
            <h2 className="text-lg font-semibold">Treatment Options</h2>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {result.treatment_plan.treatment_options.map((option, index) => (
              <TreatmentCard key={index} treatment={option} />
            ))}
          </div>
        </div>
      )}

      {/* Clinical Trials */}
      {clinicalTrials.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-4">
            <TestTube className="w-5 h-5 text-primary-600" />
            <h2 className="text-lg font-semibold">Matched Clinical Trials</h2>
            <Badge>{clinicalTrials.length} matches</Badge>
          </div>
          <div className="grid gap-4">
            {clinicalTrials.map((trial, index) => (
              <ClinicalTrialCard key={index} trial={trial} />
            ))}
          </div>
        </div>
      )}

      {/* Sources */}
      {sourcesUsed.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Sources Used</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {sourcesUsed.map((source, index) => (
                <Badge key={index} variant="default">
                  {source}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
