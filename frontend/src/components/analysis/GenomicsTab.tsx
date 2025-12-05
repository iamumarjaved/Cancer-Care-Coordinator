'use client';

import { useGenomicReport, usePatientTargetedTherapies, useAnalysisHistory } from '@/hooks';
import { Card, CardContent, CardHeader, CardTitle, Badge } from '@/components/ui';
import { Dna, Target, TestTube, AlertCircle } from 'lucide-react';
import { RunAnalysisPrompt } from './RunAnalysisPrompt';

interface GenomicsTabProps {
  patientId: string;
}

export function GenomicsTab({ patientId }: GenomicsTabProps) {
  const { data: analysisHistory, isLoading: historyLoading } = useAnalysisHistory(patientId);
  const hasCompletedAnalysis = analysisHistory && analysisHistory.analyses.some(a => a.status === 'completed');

  // Only fetch genomics data if analysis has been completed
  const { data: genomicsData, isLoading, error } = useGenomicReport(hasCompletedAnalysis ? patientId : null);
  const { data: therapiesData } = usePatientTargetedTherapies(hasCompletedAnalysis ? patientId : null);

  if (historyLoading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-32 bg-gray-200 rounded-lg" />
        <div className="h-48 bg-gray-200 rounded-lg" />
      </div>
    );
  }

  // Show prompt if no analysis has been completed
  if (!hasCompletedAnalysis) {
    return (
      <RunAnalysisPrompt
        patientId={patientId}
        tabName="Genomic Analysis"
        description="Run an AI analysis to interpret genomic data, identify actionable mutations, and find targeted therapy options."
        icon="genomics"
      />
    );
  }

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-32 bg-gray-200 rounded-lg" />
        <div className="h-48 bg-gray-200 rounded-lg" />
      </div>
    );
  }

  if (error || !genomicsData) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <AlertCircle className="w-10 h-10 mx-auto text-gray-300 mb-3" />
          <p className="text-gray-500">Genomic data not available</p>
        </CardContent>
      </Card>
    );
  }

  const { report, has_actionable_mutations, actionable_mutation_count } = genomicsData;

  return (
    <div className="space-y-6">
      {/* Summary Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Dna className="w-5 h-5 text-primary-600" />
              <CardTitle>Genomic Profile Summary</CardTitle>
            </div>
            {has_actionable_mutations && (
              <Badge variant="success">
                {actionable_mutation_count} Actionable Mutation{actionable_mutation_count > 1 ? 's' : ''}
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-500">Test Type</p>
              <p className="font-medium">{report.test_type}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Lab</p>
              <p className="font-medium">{report.lab_name}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Test Date</p>
              <p className="font-medium">{report.test_date}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Specimen</p>
              <p className="font-medium">{report.specimen_type}</p>
            </div>
          </div>
          {report.summary && (
            <p className="mt-4 text-sm text-gray-700 bg-gray-50 p-3 rounded-lg">
              {report.summary}
            </p>
          )}
        </CardContent>
      </Card>

      {/* Mutations Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Target className="w-5 h-5 text-primary-600" />
            <CardTitle>Detected Mutations</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          {report.mutations.length === 0 ? (
            <p className="text-gray-500 text-center py-4">No mutations detected</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 font-medium text-gray-600">Gene</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-600">Variant</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-600">Classification</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-600">Tier</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-600">VAF</th>
                  </tr>
                </thead>
                <tbody>
                  {report.mutations.map((mutation, i) => (
                    <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4 font-semibold text-primary-700">{mutation.gene}</td>
                      <td className="py-3 px-4">{mutation.variant}</td>
                      <td className="py-3 px-4">
                        <Badge
                          variant={
                            mutation.classification === 'pathogenic_actionable'
                              ? 'success'
                              : mutation.classification === 'pathogenic'
                              ? 'warning'
                              : 'info'
                          }
                        >
                          {mutation.classification.replace(/_/g, ' ')}
                        </Badge>
                      </td>
                      <td className="py-3 px-4">{mutation.tier || '-'}</td>
                      <td className="py-3 px-4">
                        {mutation.allele_frequency
                          ? `${(mutation.allele_frequency * 100).toFixed(1)}%`
                          : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Immunotherapy Markers */}
      {report.immunotherapy_markers && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <TestTube className="w-5 h-5 text-primary-600" />
              <CardTitle>Immunotherapy Markers</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500 mb-1">PD-L1 Expression</p>
                <p className="text-2xl font-bold text-primary-700">
                  {report.immunotherapy_markers.pdl1_expression !== undefined
                    ? `${report.immunotherapy_markers.pdl1_expression}%`
                    : 'N/A'}
                </p>
                {report.immunotherapy_markers.pdl1_interpretation && (
                  <p className="text-xs text-gray-400 mt-1">
                    {report.immunotherapy_markers.pdl1_interpretation}
                  </p>
                )}
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500 mb-1">TMB</p>
                <p className="text-2xl font-bold text-primary-700">
                  {report.immunotherapy_markers.tmb !== undefined
                    ? `${report.immunotherapy_markers.tmb}`
                    : 'N/A'}
                </p>
                {report.immunotherapy_markers.tmb_interpretation && (
                  <p className="text-xs text-gray-400 mt-1">
                    {report.immunotherapy_markers.tmb_interpretation}
                  </p>
                )}
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500 mb-1">MSI Status</p>
                <p className="text-2xl font-bold text-primary-700">
                  {report.immunotherapy_markers.msi_status || 'N/A'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Targeted Therapies */}
      {therapiesData && therapiesData.therapies.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Target className="w-5 h-5 text-green-600" />
              <CardTitle>Targeted Therapy Options</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {therapiesData.therapies.map((therapy, i) => (
                <div
                  key={i}
                  className="p-4 border border-gray-200 rounded-lg hover:border-primary-300 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-semibold text-gray-900">{therapy.drug}</p>
                      <p className="text-sm text-gray-600">{therapy.indication}</p>
                    </div>
                    <Badge variant="success">{therapy.evidence_level}</Badge>
                  </div>
                  <div className="mt-2 flex items-center gap-4 text-sm text-gray-500">
                    <span>Target: {therapy.target_mutation}</span>
                    {therapy.response_rate != null && (
                      <span>Response Rate: {
                        // If value > 1, it's already a percentage (e.g., 37.1), otherwise multiply by 100
                        therapy.response_rate > 1
                          ? `${therapy.response_rate.toFixed(0)}%`
                          : `${(therapy.response_rate * 100).toFixed(0)}%`
                      }</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
