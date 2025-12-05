'use client';

import { useState } from 'react';
import { Button } from '@/components/ui';
import { TreatmentProcedureCreate, ProcedureType } from '@/types';
import { Loader2, X } from 'lucide-react';

interface AddProcedureModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (procedure: TreatmentProcedureCreate) => Promise<void>;
  cycleId: string;
  cycleName: string;
  cycleStartDate?: string;
}

const PROCEDURE_TYPES: { value: ProcedureType; label: string }[] = [
  { value: 'infusion', label: 'Infusion' },
  { value: 'lab_check', label: 'Lab Check' },
  { value: 'imaging', label: 'Imaging' },
  { value: 'injection', label: 'Injection' },
  { value: 'oral_medication', label: 'Oral Medication' },
  { value: 'radiation_session', label: 'Radiation Session' },
  { value: 'consultation', label: 'Consultation' },
  { value: 'other', label: 'Other' },
];

const PROCEDURE_NAME_SUGGESTIONS: Record<ProcedureType, string[]> = {
  infusion: ['Chemotherapy Infusion', 'Immunotherapy Infusion', 'Maintenance Infusion', 'Hydration'],
  lab_check: ['CBC with Differential', 'Comprehensive Metabolic Panel', 'Liver Function Tests', 'Tumor Markers'],
  imaging: ['CT Scan', 'PET Scan', 'MRI', 'X-Ray', 'Ultrasound'],
  injection: ['Subcutaneous Injection', 'Intramuscular Injection', 'Growth Factor'],
  oral_medication: ['Oral Chemotherapy', 'Antiemetic', 'Supportive Care'],
  radiation_session: ['External Beam Radiation', 'Stereotactic Radiosurgery', 'Brachytherapy'],
  consultation: ['Oncology Follow-up', 'Radiology Review', 'Pharmacy Consult'],
  other: ['Other Procedure'],
};

export function AddProcedureModal({
  isOpen,
  onClose,
  onSubmit,
  cycleId,
  cycleName,
  cycleStartDate,
}: AddProcedureModalProps) {
  const [procedureType, setProcedureType] = useState<ProcedureType>('infusion');
  const [procedureName, setProcedureName] = useState('');
  const [scheduledDate, setScheduledDate] = useState('');
  const [scheduledTime, setScheduledTime] = useState('09:00');
  const [location, setLocation] = useState('Infusion Center');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Calculate day number from cycle start date
  const calculateDayNumber = (date: string): number => {
    if (!cycleStartDate || !date) return 1;
    const start = new Date(cycleStartDate);
    const scheduled = new Date(date);
    const diffTime = scheduled.getTime() - start.getTime();
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    return diffDays + 1; // Day 1 is the start date
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!procedureName || !scheduledDate) return;

    setIsSubmitting(true);
    try {
      const procedure: TreatmentProcedureCreate = {
        procedure_type: procedureType,
        procedure_name: procedureName,
        day_number: calculateDayNumber(scheduledDate),
        scheduled_date: scheduledDate,
        scheduled_time: scheduledTime || undefined,
        location: location || undefined,
      };
      await onSubmit(procedure);
      handleClose();
    } catch (error) {
      console.error('Failed to create procedure:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setProcedureType('infusion');
    setProcedureName('');
    setScheduledDate('');
    setScheduledTime('09:00');
    setLocation('Infusion Center');
    onClose();
  };

  const handleTypeChange = (type: ProcedureType) => {
    setProcedureType(type);
    // Auto-suggest first procedure name for the type
    const suggestions = PROCEDURE_NAME_SUGGESTIONS[type];
    if (suggestions && suggestions.length > 0 && !procedureName) {
      setProcedureName(suggestions[0]);
    }
  };

  // Get today's date in YYYY-MM-DD format for min date
  const today = new Date().toISOString().split('T')[0];

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={handleClose} />

      {/* Modal */}
      <div className="relative w-full max-w-md max-h-[90vh] overflow-auto bg-white rounded-xl shadow-2xl mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Add Procedure</h2>
            <p className="text-sm text-gray-500 mt-1">For: {cycleName}</p>
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
          {/* Procedure Type */}
          <div className="space-y-2">
            <label htmlFor="procedureType" className="block text-sm font-medium text-gray-700">
              Procedure Type *
            </label>
            <select
              id="procedureType"
              value={procedureType}
              onChange={(e) => handleTypeChange(e.target.value as ProcedureType)}
              className="w-full h-10 px-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              {PROCEDURE_TYPES.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          {/* Procedure Name */}
          <div className="space-y-2">
            <label htmlFor="procedureName" className="block text-sm font-medium text-gray-700">
              Procedure Name *
            </label>
            <input
              id="procedureName"
              type="text"
              value={procedureName}
              onChange={(e) => setProcedureName(e.target.value)}
              placeholder="e.g., Chemotherapy Infusion"
              list="procedureNameSuggestions"
              required
              className="w-full h-10 px-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
            <datalist id="procedureNameSuggestions">
              {PROCEDURE_NAME_SUGGESTIONS[procedureType]?.map((name) => (
                <option key={name} value={name} />
              ))}
            </datalist>
          </div>

          {/* Date Picker */}
          <div className="space-y-2">
            <label htmlFor="scheduledDate" className="block text-sm font-medium text-gray-700">
              Scheduled Date *
            </label>
            <input
              id="scheduledDate"
              type="date"
              value={scheduledDate}
              onChange={(e) => setScheduledDate(e.target.value)}
              min={today}
              required
              className="w-full h-10 px-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
            {scheduledDate && cycleStartDate && (
              <p className="text-xs text-gray-500">
                Day {calculateDayNumber(scheduledDate)} of cycle
              </p>
            )}
          </div>

          {/* Time Picker */}
          <div className="space-y-2">
            <label htmlFor="scheduledTime" className="block text-sm font-medium text-gray-700">
              Scheduled Time
            </label>
            <input
              id="scheduledTime"
              type="time"
              value={scheduledTime}
              onChange={(e) => setScheduledTime(e.target.value)}
              className="w-full h-10 px-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          {/* Location */}
          <div className="space-y-2">
            <label htmlFor="location" className="block text-sm font-medium text-gray-700">
              Location
            </label>
            <input
              id="location"
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="e.g., Infusion Center, Lab, Radiology"
              list="locationSuggestions"
              className="w-full h-10 px-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
            <datalist id="locationSuggestions">
              <option value="Infusion Center" />
              <option value="Laboratory" />
              <option value="Radiology" />
              <option value="Oncology Clinic" />
              <option value="Pharmacy" />
            </datalist>
          </div>

          {/* Footer */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <Button type="button" variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" disabled={isSubmitting || !procedureName || !scheduledDate}>
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  Creating...
                </>
              ) : (
                'Create Procedure'
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
