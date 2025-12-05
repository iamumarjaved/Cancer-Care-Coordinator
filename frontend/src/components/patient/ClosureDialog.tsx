'use client';

import { useState } from 'react';
import { Button } from '@/components/ui';
import { X, AlertTriangle, Loader2 } from 'lucide-react';
import { ClosureReason, PatientStatusUpdate } from '@/types';

interface ClosureDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (data: PatientStatusUpdate) => Promise<void>;
  patientName: string;
}

const CLOSURE_REASONS: { value: ClosureReason; label: string; description: string }[] = [
  { value: 'cured', label: 'Cured', description: 'Patient has been successfully cured' },
  { value: 'remission', label: 'In Remission', description: 'Cancer is in remission' },
  { value: 'deceased', label: 'Deceased', description: 'Patient has passed away' },
  { value: 'transferred', label: 'Transferred', description: 'Patient transferred to another facility' },
  { value: 'lost_to_followup', label: 'Lost to Follow-up', description: 'Unable to contact patient' },
  { value: 'patient_choice', label: 'Patient Choice', description: 'Patient chose to discontinue care' },
  { value: 'other', label: 'Other', description: 'Other reason (specify in notes)' },
];

export function ClosureDialog({ isOpen, onClose, onConfirm, patientName }: ClosureDialogProps) {
  const [reason, setReason] = useState<ClosureReason | ''>('');
  const [notes, setNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!reason) {
      setError('Please select a closure reason');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      await onConfirm({
        status: 'closed',
        closure: {
          reason,
          notes: notes || undefined,
        },
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to close patient file');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setReason('');
    setNotes('');
    setError(null);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={handleClose} />

      {/* Modal */}
      <div className="relative w-full max-w-md max-h-[90vh] overflow-y-auto bg-white rounded-xl shadow-2xl mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-amber-100 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-amber-600" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Close Patient File</h2>
              <p className="text-sm text-gray-500">{patientName}</p>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          <p className="text-sm text-gray-600">
            Closing this patient file will mark the patient as inactive. This action can be reversed later if needed.
          </p>

          {/* Closure Reason */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Closure Reason *
            </label>
            <div className="space-y-2">
              {CLOSURE_REASONS.map((option) => (
                <label
                  key={option.value}
                  className={`flex items-start p-3 border rounded-lg cursor-pointer transition-colors ${
                    reason === option.value
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <input
                    type="radio"
                    name="closure-reason"
                    value={option.value}
                    checked={reason === option.value}
                    onChange={(e) => setReason(e.target.value as ClosureReason)}
                    className="mt-0.5 mr-3"
                  />
                  <div>
                    <span className="text-sm font-medium text-gray-900">{option.label}</span>
                    <p className="text-xs text-gray-500">{option.description}</p>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Notes (optional)
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              rows={3}
              placeholder="Add any additional notes about the closure..."
            />
          </div>

          {/* Error */}
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 p-6 border-t bg-gray-50">
          <Button variant="ghost" onClick={handleClose}>
            Cancel
          </Button>
          <Button
            variant="danger"
            onClick={handleSubmit}
            disabled={!reason || isSubmitting}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Closing...
              </>
            ) : (
              'Close Patient File'
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
