'use client';

import { usePatientEvidence, useAnalysisHistory } from '@/hooks';
import { Card, CardContent, CardHeader, CardTitle, Badge } from '@/components/ui';
import { BookOpen, FileText, ScrollText, Clock, ExternalLink, AlertCircle } from 'lucide-react';
import { RunAnalysisPrompt } from './RunAnalysisPrompt';

interface EvidenceTabProps {
  patientId: string;
}

export function EvidenceTab({ patientId }: EvidenceTabProps) {
  const { data: analysisHistory, isLoading: historyLoading } = useAnalysisHistory(patientId);
  const hasCompletedAnalysis = analysisHistory && analysisHistory.analyses.some(a => a.status === 'completed');

  // Only fetch evidence data if analysis has been completed
  const { data, isLoading, error } = usePatientEvidence(hasCompletedAnalysis ? patientId : null);

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
        tabName="Medical Evidence"
        description="Run an AI analysis to search medical literature and clinical guidelines relevant to this patient's condition."
        icon="evidence"
      />
    );
  }

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-32 bg-gray-200 rounded-lg" />
        <div className="h-48 bg-gray-200 rounded-lg" />
        <div className="h-48 bg-gray-200 rounded-lg" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <AlertCircle className="w-10 h-10 mx-auto text-gray-300 mb-3" />
          <p className="text-gray-500">Evidence data not available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Evidence Summaries */}
      {data.evidence_summaries && data.evidence_summaries.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-primary-600" />
              <CardTitle>Evidence Summary</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {data.evidence_summaries.map((summary, i) => (
                <div
                  key={i}
                  className="p-4 bg-gray-50 rounded-lg border border-gray-100"
                >
                  <div className="flex items-start justify-between mb-2">
                    <h4 className="font-semibold text-gray-900">{summary.treatment}</h4>
                    <Badge
                      variant={
                        summary.evidence_strength.includes('1')
                          ? 'success'
                          : summary.evidence_strength.includes('2A')
                          ? 'warning'
                          : 'info'
                      }
                    >
                      {summary.evidence_strength}
                    </Badge>
                  </div>
                  <p className="text-sm text-gray-700 mb-3">{summary.summary}</p>
                  {summary.key_trials && summary.key_trials.length > 0 && (
                    <div className="mb-2">
                      <p className="text-xs font-medium text-gray-500 mb-1">Key Trials:</p>
                      <ul className="text-sm text-gray-600 space-y-1">
                        {summary.key_trials.map((trial, j) => {
                          // Handle both string and object formats from AI
                          const trialName = typeof trial === 'string' ? trial : (trial as { name?: string; result?: string }).name || '';
                          const trialResult = typeof trial === 'string' ? '' : (trial as { name?: string; result?: string }).result || '';
                          return (
                            <li key={j} className="flex items-start gap-1">
                              <span className="text-primary-500">•</span>
                              <span>
                                {trialName}
                                {trialResult && <span className="text-gray-500 ml-1">- {trialResult}</span>}
                              </span>
                            </li>
                          );
                        })}
                      </ul>
                    </div>
                  )}
                  {summary.guideline_recommendation && (
                    <p className="text-sm text-primary-700 bg-primary-50 p-2 rounded">
                      <span className="font-medium">Guideline:</span>{' '}
                      {summary.guideline_recommendation}
                    </p>
                  )}
                  {/* Also show guideline_recommendations array if present */}
                  {!summary.guideline_recommendation && (summary as { guideline_recommendations?: Array<{ guideline?: string; recommendation?: string; evidence_level?: string }> }).guideline_recommendations && (summary as { guideline_recommendations?: Array<{ guideline?: string; recommendation?: string; evidence_level?: string }> }).guideline_recommendations!.length > 0 && (
                    <div className="space-y-2">
                      {(summary as { guideline_recommendations?: Array<{ guideline?: string; recommendation?: string; evidence_level?: string }> }).guideline_recommendations!.map((gr, k) => (
                        <p key={k} className="text-sm text-primary-700 bg-primary-50 p-2 rounded">
                          <span className="font-medium">{gr.guideline || 'Guideline'}:</span>{' '}
                          {gr.recommendation}
                          {gr.evidence_level && <Badge variant="info" className="ml-2 text-xs">{gr.evidence_level}</Badge>}
                        </p>
                      ))}
                    </div>
                  )}
                  {summary.applicability_to_patient && (
                    <p className="text-xs text-gray-500 mt-2 italic">
                      <span className="font-medium">Applicability:</span> {summary.applicability_to_patient}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Guidelines */}
      {data.guidelines && data.guidelines.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <ScrollText className="w-5 h-5 text-primary-600" />
              <CardTitle>Clinical Guidelines</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {data.guidelines.map((guideline, i) => (
                <div
                  key={i}
                  className="p-4 border border-gray-200 rounded-lg hover:border-primary-300 transition-colors"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <p className="font-medium text-gray-900">{guideline.guideline}</p>
                      {guideline.version && (
                        <p className="text-xs text-gray-500">{guideline.version}</p>
                      )}
                    </div>
                    <Badge
                      variant={
                        guideline.evidence_level.includes('1')
                          ? 'success'
                          : guideline.evidence_level.includes('2A')
                          ? 'warning'
                          : 'info'
                      }
                    >
                      {guideline.evidence_level}
                    </Badge>
                  </div>
                  <p className="text-sm text-gray-700">{guideline.recommendation}</p>
                  {guideline.notes && (
                    <p className="text-xs text-gray-500 mt-2 italic">{guideline.notes}</p>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Updates */}
      {data.recent_updates && data.recent_updates.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-primary-600" />
              <CardTitle>Recent Updates</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {data.recent_updates.map((update, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <span className="w-2 h-2 mt-1.5 rounded-full bg-primary-500 flex-shrink-0" />
                  <span className="text-gray-700">{update}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Publications */}
      {data.publications && data.publications.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-primary-600" />
                <CardTitle>Relevant Publications</CardTitle>
              </div>
              <Badge variant="info">{data.publications.length} papers</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {data.publications.map((pub, i) => (
                <div
                  key={i}
                  className="p-4 border border-gray-200 rounded-lg hover:border-primary-300 transition-colors"
                >
                  <h4 className="font-medium text-gray-900 mb-1">{pub.title}</h4>
                  <p className="text-sm text-gray-500 mb-2">
                    {pub.authors && pub.authors.length > 0 && (
                      <>
                        {pub.authors.slice(0, 3).join(', ')}
                        {pub.authors.length > 3 && ' et al.'}
                        {(pub.journal || pub.publication_date) && ' • '}
                      </>
                    )}
                    {pub.journal}
                    {pub.publication_date && ` (${pub.publication_date})`}
                  </p>
                  {pub.abstract && (
                    <p className="text-sm text-gray-600 line-clamp-3 mb-2">{pub.abstract}</p>
                  )}
                  {pub.relevance && (
                    <p className="text-sm text-primary-700 bg-primary-50 p-2 rounded mb-2">
                      {pub.relevance}
                    </p>
                  )}
                  <a
                    href={pub.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-sm text-primary-600 hover:text-primary-700"
                  >
                    View on PubMed
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Search Terms Used */}
      {data.search_terms && data.search_terms.length > 0 && (
        <div className="text-sm text-gray-500">
          <span className="font-medium">Search terms used:</span>{' '}
          {data.search_terms.join(', ')}
        </div>
      )}
    </div>
  );
}
