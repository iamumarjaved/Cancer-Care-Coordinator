'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { useUser } from '@clerk/nextjs';
import { usePatient, useUpdatePatientStatus } from '@/hooks/usePatients';
import { api } from '@/lib/api';
import { Card, CardContent, Button, Badge, Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui';
import { Chat } from '@/components/chat/Chat';
import { SummaryTab } from '@/components/analysis/SummaryTab';
import { GenomicsTab } from '@/components/analysis/GenomicsTab';
import { TrialsTab } from '@/components/analysis/TrialsTab';
import { EvidenceTab } from '@/components/analysis/EvidenceTab';
import { TreatmentTab } from '@/components/analysis/TreatmentTab';
import { ProceduresTab } from '@/components/procedures/ProceduresTab';
import { ClinicalNotesTab } from '@/components/clinical-notes/ClinicalNotesTab';
import { EditPatientModal } from '@/components/patient/EditPatientModal';
import { ClosureDialog } from '@/components/patient/ClosureDialog';
import { PatientStatusUpdate, ClosureReason } from '@/types';
import {
  ArrowLeft,
  Play,
  User,
  Dna,
  FlaskConical,
  BookOpen,
  Pill,
  MessageSquare,
  CalendarDays,
  Pencil,
  FileX,
  RefreshCw,
  Stethoscope,
} from 'lucide-react';

const CLOSURE_REASON_LABELS: Record<ClosureReason, string> = {
  deceased: 'Deceased',
  cured: 'Cured',
  remission: 'In Remission',
  transferred: 'Transferred',
  lost_to_followup: 'Lost to Follow-up',
  patient_choice: 'Patient Choice',
  other: 'Other',
};

export default function PatientDetailPage() {
  const params = useParams();
  const patientId = params.id as string;
  const [showEditModal, setShowEditModal] = useState(false);
  const [showClosureDialog, setShowClosureDialog] = useState(false);
  const hasNotifiedOpenRef = useRef(false);

  const { user } = useUser();
  const { data: patient, isLoading, error, refetch } = usePatient(patientId);
  const updateStatus = useUpdatePatientStatus();

  // Send notification when patient file is opened
  useEffect(() => {
    const userEmail = user?.primaryEmailAddress?.emailAddress;
    if (patient && userEmail && !hasNotifiedOpenRef.current) {
      hasNotifiedOpenRef.current = true;
      api.notifyPatientOpened(patientId, userEmail).catch((err) => {
        console.error('Failed to send patient opened notification:', err);
      });
    }
  }, [patient, user, patientId]);

  const handleClosePatient = async (statusUpdate: PatientStatusUpdate) => {
    await updateStatus.mutateAsync({ id: patientId, statusUpdate });

    // Send notification when patient file is closed
    const userEmail = user?.primaryEmailAddress?.emailAddress;
    if (userEmail) {
      api.notifyPatientClosed(patientId, userEmail).catch((err) => {
        console.error('Failed to send patient closed notification:', err);
      });
    }

    refetch();
  };

  const handleReopenPatient = async () => {
    await updateStatus.mutateAsync({
      id: patientId,
      statusUpdate: { status: 'active' },
    });
    refetch();
  };

  const isPatientClosed = patient?.status === 'closed';

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-8 bg-gray-200 rounded w-1/4" />
        <div className="h-12 bg-gray-200 rounded w-full" />
        <div className="h-96 bg-gray-200 rounded" />
      </div>
    );
  }

  if (error || !patient) {
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
          <Link href="/patients">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="w-4 h-4" />
            </Button>
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-gray-900">
                {patient.first_name} {patient.last_name}
              </h1>
              {isPatientClosed ? (
                <Badge variant="default" className="bg-gray-100 text-gray-700">
                  Closed: {patient.closure_reason ? CLOSURE_REASON_LABELS[patient.closure_reason] : 'Unknown'}
                </Badge>
              ) : (
                <Badge variant="default" className="bg-green-100 text-green-700">
                  Active
                </Badge>
              )}
            </div>
            <p className="text-gray-600">Patient ID: {patient.id}</p>
            {isPatientClosed && patient.closure_notes && (
              <p className="text-sm text-gray-500 mt-1">Note: {patient.closure_notes}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {isPatientClosed ? (
            <Button
              variant="outline"
              onClick={handleReopenPatient}
              disabled={updateStatus.isPending}
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Reopen File
            </Button>
          ) : (
            <>
              <Button variant="outline" onClick={() => setShowEditModal(true)}>
                <Pencil className="w-4 h-4 mr-2" />
                Edit Patient
              </Button>
              <Button
                variant="outline"
                onClick={() => setShowClosureDialog(true)}
                className="text-amber-600 border-amber-300 hover:bg-amber-50"
              >
                <FileX className="w-4 h-4 mr-2" />
                Close File
              </Button>
              <Link href={`/patients/${patientId}/analysis`}>
                <Button>
                  <Play className="w-4 h-4 mr-2" />
                  Run Analysis
                </Button>
              </Link>
            </>
          )}
        </div>
      </div>

      {/* Tabbed Content */}
      <Tabs defaultValue="summary" className="w-full">
        <TabsList className="w-full justify-start gap-1 overflow-x-auto">
          <TabsTrigger value="summary" className="flex items-center gap-1.5">
            <User className="w-4 h-4" />
            Summary
          </TabsTrigger>
          <TabsTrigger value="notes" className="flex items-center gap-1.5">
            <Stethoscope className="w-4 h-4" />
            Notes
          </TabsTrigger>
          <TabsTrigger value="genomics" className="flex items-center gap-1.5">
            <Dna className="w-4 h-4" />
            Genomics
          </TabsTrigger>
          <TabsTrigger value="trials" className="flex items-center gap-1.5">
            <FlaskConical className="w-4 h-4" />
            Trials
          </TabsTrigger>
          <TabsTrigger value="evidence" className="flex items-center gap-1.5">
            <BookOpen className="w-4 h-4" />
            Evidence
          </TabsTrigger>
          <TabsTrigger value="treatment" className="flex items-center gap-1.5">
            <Pill className="w-4 h-4" />
            Treatment
          </TabsTrigger>
          <TabsTrigger value="schedule" className="flex items-center gap-1.5">
            <CalendarDays className="w-4 h-4" />
            Schedule
          </TabsTrigger>
          <TabsTrigger value="chat" className="flex items-center gap-1.5">
            <MessageSquare className="w-4 h-4" />
            Chat
          </TabsTrigger>
        </TabsList>

        <TabsContent value="summary">
          <SummaryTab patientId={patientId} />
        </TabsContent>

        <TabsContent value="notes">
          <ClinicalNotesTab patientId={patientId} />
        </TabsContent>

        <TabsContent value="genomics">
          <GenomicsTab patientId={patientId} />
        </TabsContent>

        <TabsContent value="trials">
          <TrialsTab patientId={patientId} />
        </TabsContent>

        <TabsContent value="evidence">
          <EvidenceTab patientId={patientId} />
        </TabsContent>

        <TabsContent value="treatment">
          <TreatmentTab patientId={patientId} />
        </TabsContent>

        <TabsContent value="schedule">
          <ProceduresTab patientId={patientId} />
        </TabsContent>

        <TabsContent value="chat">
          <div className="max-w-3xl mx-auto">
            <Chat patientId={patientId} />
          </div>
        </TabsContent>
      </Tabs>

      {/* Edit Patient Modal */}
      {patient && (
        <EditPatientModal
          isOpen={showEditModal}
          onClose={() => setShowEditModal(false)}
          onSuccess={() => refetch()}
          patient={patient}
        />
      )}

      {/* Closure Dialog */}
      {patient && (
        <ClosureDialog
          isOpen={showClosureDialog}
          onClose={() => setShowClosureDialog(false)}
          onConfirm={handleClosePatient}
          patientName={`${patient.first_name} ${patient.last_name}`}
        />
      )}
    </div>
  );
}
