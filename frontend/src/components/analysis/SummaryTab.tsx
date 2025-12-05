'use client';

import { useState } from 'react';
import { usePatient, useAnalysisHistory } from '@/hooks';
import { Card, CardContent, CardHeader, CardTitle, Badge, Button, Dialog, DialogHeader, DialogContent } from '@/components/ui';
import { calculateAge, formatDate, formatCancerStage } from '@/lib/utils';
import {
  User,
  Activity,
  AlertTriangle,
  Pill,
  History,
  Play,
  CheckCircle,
  Clock,
  XCircle,
  FileText,
  Lightbulb,
} from 'lucide-react';
import Link from 'next/link';

// Type for analysis history items (from getPatientAnalysisHistory API)
interface AnalysisHistoryItem {
  id: number;
  analysis_type: string;
  status: string;
  summary: string;
  key_findings: string[];
  confidence_score: number | null;
  created_at: string | null;
  completed_at: string | null;
}

interface SummaryTabProps {
  patientId: string;
}

export function SummaryTab({ patientId }: SummaryTabProps) {
  const { data: patient, isLoading, error } = usePatient(patientId);
  const { data: analysisHistory } = useAnalysisHistory(patientId);
  const [selectedAnalysis, setSelectedAnalysis] = useState<AnalysisHistoryItem | null>(null);

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-32 bg-gray-200 rounded-lg" />
        <div className="h-48 bg-gray-200 rounded-lg" />
      </div>
    );
  }

  if (error || !patient) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <p className="text-gray-500">Patient data not available</p>
        </CardContent>
      </Card>
    );
  }

  const age = calculateAge(patient.date_of_birth);
  const ecogStatus = patient.ecog_status ?? 1;
  const cancerDetails = patient.cancer_details;
  const comorbidities = patient.comorbidities || [];
  const currentMedications = patient.current_medications || [];

  return (
    <div className="space-y-6">
      {/* Demographics */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <User className="w-5 h-5 text-primary-600" />
            <CardTitle>Demographics</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-500">Age</p>
              <p className="font-medium">{age} years</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Sex</p>
              <p className="font-medium">{patient.sex || 'Unknown'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">ECOG Status</p>
              <Badge variant={ecogStatus <= 1 ? 'success' : 'warning'}>
                ECOG {ecogStatus}
              </Badge>
            </div>
            <div>
              <p className="text-sm text-gray-500">Date of Birth</p>
              <p className="font-medium">{formatDate(patient.date_of_birth)}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Cancer Details */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-primary-600" />
            <CardTitle>Cancer Details</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          {cancerDetails ? (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Cancer Type</p>
                  <p className="font-medium">{cancerDetails.cancer_type}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Subtype</p>
                  <p className="font-medium">{cancerDetails.subtype || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Stage</p>
                  {cancerDetails.stage ? (
                    <Badge variant="info">{formatCancerStage(cancerDetails.stage)}</Badge>
                  ) : (
                    <p className="font-medium text-gray-400">N/A</p>
                  )}
                </div>
                <div>
                  <p className="text-sm text-gray-500">TNM Staging</p>
                  <p className="font-medium">{cancerDetails.tnm_staging || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Primary Site</p>
                  <p className="font-medium">{cancerDetails.primary_site || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Diagnosis Date</p>
                  <p className="font-medium">
                    {cancerDetails.diagnosis_date
                      ? formatDate(cancerDetails.diagnosis_date)
                      : 'N/A'}
                  </p>
                </div>
              </div>

              {cancerDetails.metastases && cancerDetails.metastases.length > 0 && (
                <div className="mt-4">
                  <p className="text-sm text-gray-500 mb-2">Metastases</p>
                  <div className="flex flex-wrap gap-2">
                    {cancerDetails.metastases.map((m, i) => (
                      <Badge key={i} variant="warning">
                        {m}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-6">
              <Activity className="w-10 h-10 mx-auto text-gray-300 mb-2" />
              <p className="text-gray-500 text-sm">Cancer details not yet entered</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Comorbidities */}
      {comorbidities.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-warning-500" />
              <CardTitle>Comorbidities</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {comorbidities.map((c, i) => (
                <div key={i} className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between">
                    <p className="font-medium">{c.condition}</p>
                    <Badge
                      variant={
                        c.severity === 'mild'
                          ? 'success'
                          : c.severity === 'moderate'
                          ? 'warning'
                          : 'danger'
                      }
                    >
                      {c.severity}
                    </Badge>
                  </div>
                  {c.treatment_implications && c.treatment_implications.length > 0 && (
                    <ul className="mt-2 text-sm text-gray-600">
                      {c.treatment_implications.map((impl, j) => (
                        <li key={j} className="flex items-start gap-1">
                          <span className="text-gray-400">•</span>
                          {impl}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Analysis History */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <History className="w-5 h-5 text-primary-600" />
              <CardTitle>Analysis History</CardTitle>
            </div>
            {analysisHistory && analysisHistory.total > 0 && (
              <Badge variant="info">{analysisHistory.total} analyses</Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {!analysisHistory || analysisHistory.analyses.length === 0 ? (
            <div className="text-center py-6">
              <History className="w-10 h-10 mx-auto text-gray-300 mb-2" />
              <p className="text-gray-500 text-sm">No analyses yet</p>
              <Link href={`/patients/${patientId}/analysis`}>
                <Button variant="outline" size="sm" className="mt-3">
                  <Play className="w-3 h-3 mr-1" />
                  Run First Analysis
                </Button>
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {analysisHistory.analyses.map((analysis) => (
                <button
                  key={analysis.id}
                  onClick={() => setSelectedAnalysis(analysis)}
                  className={`w-full text-left p-3 rounded-lg border transition-colors cursor-pointer ${
                    analysis.status === 'error'
                      ? 'bg-red-50 border-red-200 hover:border-red-300'
                      : 'bg-gray-50 border-gray-100 hover:border-primary-300 hover:bg-gray-100'
                  }`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {analysis.status === 'completed' ? (
                        <CheckCircle className="w-4 h-4 text-green-500" />
                      ) : analysis.status === 'error' ? (
                        <XCircle className="w-4 h-4 text-red-500" />
                      ) : (
                        <Clock className="w-4 h-4 text-yellow-500" />
                      )}
                      <span className="text-sm font-medium capitalize">
                        {analysis.analysis_type} Analysis
                      </span>
                      {analysis.status === 'error' && (
                        <Badge variant="danger" className="text-xs">Failed</Badge>
                      )}
                    </div>
                    <span className="text-xs text-gray-500">
                      {analysis.completed_at
                        ? formatDate(analysis.completed_at)
                        : analysis.created_at
                        ? formatDate(analysis.created_at)
                        : 'Unknown date'}
                    </span>
                  </div>
                  {analysis.summary && (
                    <p className={`text-sm line-clamp-2 ${
                      analysis.status === 'error' ? 'text-red-600' : 'text-gray-600'
                    }`}>{analysis.summary}</p>
                  )}
                  {analysis.key_findings && analysis.key_findings.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {analysis.key_findings.slice(0, 2).map((finding, i) => (
                        <Badge key={i} variant="info" className="text-xs">
                          {finding.length > 40 ? finding.substring(0, 40) + '...' : finding}
                        </Badge>
                      ))}
                      {analysis.key_findings.length > 2 && (
                        <Badge variant="info" className="text-xs">
                          +{analysis.key_findings.length - 2} more
                        </Badge>
                      )}
                    </div>
                  )}
                  <p className="text-xs text-primary-600 mt-2">Click to view details</p>
                </button>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Current Medications */}
      {currentMedications.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Pill className="w-5 h-5 text-primary-600" />
              <CardTitle>Current Medications</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {currentMedications.map((med, i) => (
                <Badge key={i} variant="info">
                  {med}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Analysis Details Dialog */}
      <Dialog
        open={!!selectedAnalysis}
        onClose={() => setSelectedAnalysis(null)}
        className="max-w-2xl"
      >
        {selectedAnalysis && (
          <>
            <DialogHeader onClose={() => setSelectedAnalysis(null)}>
              <div className="flex items-center gap-2">
                {selectedAnalysis.status === 'completed' ? (
                  <CheckCircle className="w-5 h-5 text-green-500" />
                ) : selectedAnalysis.status === 'error' ? (
                  <XCircle className="w-5 h-5 text-red-500" />
                ) : (
                  <Clock className="w-5 h-5 text-yellow-500" />
                )}
                <span className="capitalize">{selectedAnalysis.analysis_type} Analysis</span>
              </div>
            </DialogHeader>
            <DialogContent className="space-y-4">
              {/* Date and Status */}
              <div className="flex items-center justify-between text-sm text-gray-500">
                <span>
                  {selectedAnalysis.completed_at
                    ? formatDate(selectedAnalysis.completed_at)
                    : selectedAnalysis.created_at
                    ? formatDate(selectedAnalysis.created_at)
                    : 'Unknown date'}
                </span>
                <Badge variant={selectedAnalysis.status === 'completed' ? 'success' : selectedAnalysis.status === 'error' ? 'danger' : 'warning'}>
                  {selectedAnalysis.status}
                </Badge>
              </div>

              {/* Summary */}
              {selectedAnalysis.summary && (
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <FileText className="w-4 h-4 text-primary-600" />
                    <h3 className="font-semibold text-gray-900">Summary</h3>
                  </div>
                  <p className="text-sm text-gray-700 leading-relaxed">
                    {selectedAnalysis.summary}
                  </p>
                </div>
              )}

              {/* Key Findings */}
              {selectedAnalysis.key_findings && selectedAnalysis.key_findings.length > 0 && (
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Lightbulb className="w-4 h-4 text-yellow-500" />
                    <h3 className="font-semibold text-gray-900">Key Findings</h3>
                  </div>
                  <ul className="space-y-1.5">
                    {selectedAnalysis.key_findings.map((finding, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                        <span className="text-primary-600 mt-1">•</span>
                        <span>{finding}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Confidence Score */}
              {selectedAnalysis.confidence_score !== null && (
                <div className="pt-2 border-t">
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">Confidence Score:</span>{' '}
                    {Math.round(selectedAnalysis.confidence_score * 100)}%
                  </p>
                </div>
              )}
            </DialogContent>
          </>
        )}
      </Dialog>
    </div>
  );
}
