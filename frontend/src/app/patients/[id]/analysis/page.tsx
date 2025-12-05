'use client';

import { useParams } from 'next/navigation';
import Link from 'next/link';
import { useUser } from '@clerk/nextjs';
import { usePatient } from '@/hooks/usePatients';
import { useRunAnalysis, useActiveAnalysis, useStopAnalysis, useStreamingAnalysis } from '@/hooks/useAnalysis';
import { AnalysisProgressComponent } from '@/components/analysis/AnalysisProgress';
import { AnalysisResults } from '@/components/analysis/AnalysisResults';
import { Card, CardContent, CardHeader, CardTitle, Button, Badge } from '@/components/ui';
import { ArrowLeft, Play, User, StopCircle, Loader2 } from 'lucide-react';
import { useState, useEffect, useRef } from 'react';

export default function PatientAnalysisPage() {
  const params = useParams();
  const patientId = params.id as string;

  const { user } = useUser();
  const { data: patient, isLoading: patientLoading } = usePatient(patientId);
  const { data: activeAnalysis, isLoading: checkingActive } = useActiveAnalysis(patientId);
  const { runAnalysis, progress, result, error, isLoading } = useRunAnalysis(patientId);
  const streaming = useStreamingAnalysis();
  const stopAnalysis = useStopAnalysis();

  const [includeTrials, setIncludeTrials] = useState(true);
  const [includeEvidence, setIncludeEvidence] = useState(true);
  const [activeRequestId, setActiveRequestId] = useState<string | null>(null);
  const hasReconnectedRef = useRef(false);

  // Reconnect to active analysis if one exists on page load
  useEffect(() => {
    if (activeAnalysis?.request_id && !hasReconnectedRef.current && !streaming.isStreaming && !streaming.result) {
      hasReconnectedRef.current = true;
      setActiveRequestId(activeAnalysis.request_id);
      streaming.startStreaming(activeAnalysis.request_id);
    }
  }, [activeAnalysis, streaming]);

  // Reset reconnect flag when analysis completes
  useEffect(() => {
    if (streaming.result || streaming.error) {
      hasReconnectedRef.current = false;
      setActiveRequestId(null);
    }
  }, [streaming.result, streaming.error]);

  const handleRunAnalysis = async () => {
    hasReconnectedRef.current = false;
    const userEmail = user?.primaryEmailAddress?.emailAddress;
    const requestId = await runAnalysis({
      include_trials: includeTrials,
      include_evidence: includeEvidence,
      user_email: userEmail,
    });
    if (requestId) {
      setActiveRequestId(requestId);
    }
  };

  const handleStopAnalysis = async () => {
    const requestIdToStop = activeRequestId || activeAnalysis?.request_id;
    if (requestIdToStop) {
      try {
        await stopAnalysis.mutateAsync(requestIdToStop);
        streaming.stopStreaming();
        setActiveRequestId(null);
        hasReconnectedRef.current = false;
      } catch (err) {
        console.error('Failed to stop analysis:', err);
      }
    }
  };

  // Use combined progress from either source
  const currentProgress = streaming.progress || progress;
  const currentResult = streaming.result || result;
  const currentError = streaming.error || error;
  const isAnalysisRunning = isLoading || streaming.isStreaming || (activeAnalysis && !currentResult && !currentError);

  if (patientLoading || checkingActive) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-8 bg-gray-200 rounded w-1/4" />
        <Card>
          <CardContent className="p-6 h-64" />
        </Card>
      </div>
    );
  }

  if (!patient) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">Patient not found</p>
        <Link href="/patients">
          <Button variant="outline" className="mt-4">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Patients
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href={`/patients/${patientId}`}>
            <Button variant="ghost" size="sm">
              <ArrowLeft className="w-4 h-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Analysis: {patient.first_name} {patient.last_name}
            </h1>
            <p className="text-gray-600">
              AI-powered comprehensive analysis
            </p>
          </div>
        </div>
        {/* Stop Analysis Button */}
        {isAnalysisRunning && (
          <Button
            variant="outline"
            onClick={handleStopAnalysis}
            disabled={stopAnalysis.isPending}
            className="text-red-600 border-red-300 hover:bg-red-50"
          >
            {stopAnalysis.isPending ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <StopCircle className="w-4 h-4 mr-2" />
            )}
            Stop Analysis
          </Button>
        )}
      </div>

      {/* Patient Summary Card */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
              <User className="w-6 h-6 text-primary-600" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="font-medium">{patient.cancer_details?.cancer_type || 'Unknown'}</span>
                {patient.cancer_details?.stage && <Badge>{patient.cancer_details.stage}</Badge>}
                <Badge variant={patient.ecog_status <= 1 ? 'success' : 'warning'}>
                  ECOG {patient.ecog_status ?? 'N/A'}
                </Badge>
              </div>
              <p className="text-sm text-gray-600">
                {patient.cancer_details?.subtype || 'Subtype unknown'} • {patient.comorbidities?.length || 0} comorbidities
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Analysis Controls - Show only when not running and no result */}
      {!isAnalysisRunning && !currentResult && (
        <Card>
          <CardHeader>
            <CardTitle>Configure Analysis</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-gray-600">
              This analysis will evaluate the patient's medical history, genomic profile,
              and match them to clinical trials and treatment options.
            </p>

            <div className="space-y-3">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={includeTrials}
                  onChange={(e) => setIncludeTrials(e.target.checked)}
                  className="rounded border-gray-300"
                />
                <span className="text-sm">Include Clinical Trial Matching</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={includeEvidence}
                  onChange={(e) => setIncludeEvidence(e.target.checked)}
                  className="rounded border-gray-300"
                />
                <span className="text-sm">Include Medical Literature Search</span>
              </label>
            </div>

            <Button onClick={handleRunAnalysis} disabled={isLoading} className="w-full">
              <Play className="w-4 h-4 mr-2" />
              {isLoading ? 'Starting Analysis...' : 'Start Analysis'}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Progress - Show when running */}
      {isAnalysisRunning && currentProgress && (
        <AnalysisProgressComponent progress={currentProgress} />
      )}

      {/* Reconnecting indicator */}
      {isAnalysisRunning && !currentProgress && activeAnalysis && (
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-3">
              <Loader2 className="w-5 h-5 animate-spin text-primary-600" />
              <div>
                <p className="font-medium">Analysis in Progress</p>
                <p className="text-sm text-gray-600">
                  Reconnecting to analysis stream... ({activeAnalysis.progress_percent}% complete)
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Error */}
      {currentError && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4">
            <p className="text-red-700">Error: {currentError.message}</p>
            <Button
              variant="outline"
              onClick={handleRunAnalysis}
              className="mt-4"
            >
              Try Again
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Results */}
      {currentResult && <AnalysisResults result={currentResult} />}
    </div>
  );
}
