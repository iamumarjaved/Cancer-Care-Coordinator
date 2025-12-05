'use client';

import { useState } from 'react';
import { useClinicalNotes, useDeleteClinicalNote } from '@/hooks';
import { Card, CardContent, CardHeader, CardTitle, Badge, Button } from '@/components/ui';
import { FileText, Plus, Trash2, AlertCircle, Stethoscope, FlaskConical, ImageIcon, TrendingUp, AlertTriangle } from 'lucide-react';
import { AddClinicalNoteModal } from './AddClinicalNoteModal';
import type { ClinicalNoteType } from '@/types';

interface ClinicalNotesTabProps {
  patientId: string;
}

const NOTE_TYPE_CONFIG: Record<ClinicalNoteType, { label: string; icon: React.ReactNode; variant: 'default' | 'info' | 'success' | 'warning' }> = {
  general: { label: 'General', icon: <FileText className="w-3 h-3" />, variant: 'default' },
  lab_result: { label: 'Lab Result', icon: <FlaskConical className="w-3 h-3" />, variant: 'info' },
  imaging: { label: 'Imaging', icon: <ImageIcon className="w-3 h-3" />, variant: 'info' },
  treatment_response: { label: 'Treatment Response', icon: <TrendingUp className="w-3 h-3" />, variant: 'success' },
  side_effect: { label: 'Side Effect', icon: <AlertTriangle className="w-3 h-3" />, variant: 'warning' },
};

export function ClinicalNotesTab({ patientId }: ClinicalNotesTabProps) {
  const [showAddModal, setShowAddModal] = useState(false);
  const { data, isLoading, error } = useClinicalNotes(patientId);
  const deleteNote = useDeleteClinicalNote();

  const handleDelete = async (noteId: string) => {
    if (confirm('Are you sure you want to delete this note?')) {
      await deleteNote.mutateAsync({ patientId, noteId });
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-12 bg-gray-200 rounded-lg" />
        <div className="h-32 bg-gray-200 rounded-lg" />
        <div className="h-32 bg-gray-200 rounded-lg" />
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <AlertCircle className="w-10 h-10 mx-auto text-gray-300 mb-3" />
          <p className="text-gray-500">Failed to load clinical notes</p>
        </CardContent>
      </Card>
    );
  }

  const notes = data?.notes || [];

  return (
    <div className="space-y-6">
      {/* Header with Add Button */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Stethoscope className="w-5 h-5 text-primary-600" />
          <h3 className="text-lg font-semibold text-gray-900">Clinical Notes</h3>
          {notes.length > 0 && (
            <Badge variant="info">{notes.length} note{notes.length !== 1 ? 's' : ''}</Badge>
          )}
        </div>
        <Button variant="primary" onClick={() => setShowAddModal(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Add Note
        </Button>
      </div>

      {/* Notes List */}
      {notes.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <FileText className="w-12 h-12 mx-auto text-gray-300 mb-4" />
            <h4 className="text-lg font-medium text-gray-900 mb-2">No Clinical Notes Yet</h4>
            <p className="text-gray-500 mb-4">
              Add clinical observations, test results, and treatment updates that will be used in AI analysis.
            </p>
            <Button variant="primary" onClick={() => setShowAddModal(true)}>
              <Plus className="w-4 h-4 mr-2" />
              Add First Note
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {notes.map((note) => {
            const typeConfig = NOTE_TYPE_CONFIG[note.note_type as ClinicalNoteType] || NOTE_TYPE_CONFIG.general;
            return (
              <Card key={note.id} className="hover:border-primary-200 transition-colors">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge variant={typeConfig.variant} className="flex items-center gap-1">
                          {typeConfig.icon}
                          {typeConfig.label}
                        </Badge>
                        <span className="text-xs text-gray-500">{formatDate(note.created_at)}</span>
                        {note.created_by && (
                          <span className="text-xs text-gray-400">by {note.created_by}</span>
                        )}
                      </div>
                      <p className="text-gray-800 whitespace-pre-wrap">{note.note_text}</p>
                    </div>
                    <button
                      onClick={() => handleDelete(note.id)}
                      className="ml-4 p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                      title="Delete note"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Info Banner */}
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm text-blue-800 font-medium">Notes are used in AI Analysis</p>
              <p className="text-sm text-blue-700">
                Clinical notes you add here will be included in future AI analyses to provide more accurate treatment recommendations and insights.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Add Modal */}
      <AddClinicalNoteModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        patientId={patientId}
      />
    </div>
  );
}
