'use client';

import { useState } from 'react';
import { Button } from '@/components/ui';
import { useCreateClinicalNote } from '@/hooks';
import { Loader2, X } from 'lucide-react';
import type { ClinicalNoteType, ClinicalNoteCreate } from '@/types';

interface AddClinicalNoteModalProps {
  isOpen: boolean;
  onClose: () => void;
  patientId: string;
}

const NOTE_TYPES: { value: ClinicalNoteType; label: string }[] = [
  { value: 'general', label: 'General Note' },
  { value: 'lab_result', label: 'Lab Result' },
  { value: 'imaging', label: 'Imaging Finding' },
  { value: 'treatment_response', label: 'Treatment Response' },
  { value: 'side_effect', label: 'Side Effect / Adverse Event' },
];

export function AddClinicalNoteModal({
  isOpen,
  onClose,
  patientId,
}: AddClinicalNoteModalProps) {
  const [noteType, setNoteType] = useState<ClinicalNoteType>('general');
  const [noteText, setNoteText] = useState('');
  const [createdBy, setCreatedBy] = useState('');

  const createNote = useCreateClinicalNote();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!noteText.trim()) return;

    try {
      const note: ClinicalNoteCreate = {
        note_text: noteText.trim(),
        note_type: noteType,
        created_by: createdBy.trim() || undefined,
      };
      await createNote.mutateAsync({ patientId, note });
      handleClose();
    } catch (error) {
      console.error('Failed to create clinical note:', error);
    }
  };

  const handleClose = () => {
    setNoteType('general');
    setNoteText('');
    setCreatedBy('');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={handleClose} />

      {/* Modal */}
      <div className="relative w-full max-w-lg max-h-[90vh] overflow-auto bg-white rounded-xl shadow-2xl mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Add Clinical Note</h2>
            <p className="text-sm text-gray-500 mt-1">
              This note will be used in future AI analyses
            </p>
          </div>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Note Type */}
          <div className="space-y-2">
            <label htmlFor="noteType" className="block text-sm font-medium text-gray-700">
              Note Type *
            </label>
            <select
              id="noteType"
              value={noteType}
              onChange={(e) => setNoteType(e.target.value as ClinicalNoteType)}
              className="w-full h-10 px-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              {NOTE_TYPES.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          {/* Note Text */}
          <div className="space-y-2">
            <label htmlFor="noteText" className="block text-sm font-medium text-gray-700">
              Note *
            </label>
            <textarea
              id="noteText"
              value={noteText}
              onChange={(e) => setNoteText(e.target.value)}
              placeholder="e.g., CT scan shows positive results - tumor reduced by 30%. Patient tolerating treatment well."
              required
              rows={5}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none"
            />
            <p className="text-xs text-gray-500">
              Be specific and include relevant clinical details, measurements, and observations.
            </p>
          </div>

          {/* Created By */}
          <div className="space-y-2">
            <label htmlFor="createdBy" className="block text-sm font-medium text-gray-700">
              Added By (Optional)
            </label>
            <input
              id="createdBy"
              type="text"
              value={createdBy}
              onChange={(e) => setCreatedBy(e.target.value)}
              placeholder="e.g., Dr. Smith"
              className="w-full h-10 px-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          {/* Footer */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <Button type="button" variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              disabled={createNote.isPending || !noteText.trim()}
            >
              {createNote.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  Adding...
                </>
              ) : (
                'Add Note'
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
