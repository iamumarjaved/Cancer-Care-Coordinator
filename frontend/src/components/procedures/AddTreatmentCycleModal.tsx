'use client';

import { useState } from 'react';
import { TreatmentCycleCreate, TreatmentType } from '@/types';
import { Button } from '@/components/ui';
import { X, Loader2 } from 'lucide-react';

interface AddTreatmentCycleModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (cycle: TreatmentCycleCreate) => Promise<void>;
  patientId: string;
}

const TREATMENT_TYPES: { value: TreatmentType; label: string }[] = [
  { value: 'chemotherapy', label: 'Chemotherapy' },
  { value: 'immunotherapy', label: 'Immunotherapy' },
  { value: 'targeted_therapy', label: 'Targeted Therapy' },
  { value: 'radiation', label: 'Radiation' },
  { value: 'surgery', label: 'Surgery' },
];

export function AddTreatmentCycleModal({
  isOpen,
  onClose,
  onSubmit,
  patientId,
}: AddTreatmentCycleModalProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState<TreatmentCycleCreate>({
    treatment_name: '',
    treatment_type: 'chemotherapy',
    cycle_number: 1,
    start_date: new Date().toISOString().split('T')[0],
    regimen: '',
    dose: '',
  });

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await onSubmit(formData);
      onClose();
      // Reset form
      setFormData({
        treatment_name: '',
        treatment_type: 'chemotherapy',
        cycle_number: 1,
        start_date: new Date().toISOString().split('T')[0],
        regimen: '',
        dose: '',
      });
    } catch (error) {
      console.error('Failed to create treatment cycle:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold">Add Treatment Cycle</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Treatment Name *
            </label>
            <input
              type="text"
              required
              className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              placeholder="e.g., FOLFOX, Pembrolizumab, Carboplatin/Paclitaxel"
              value={formData.treatment_name}
              onChange={(e) => setFormData({ ...formData, treatment_name: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Treatment Type *
              </label>
              <select
                required
                className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                value={formData.treatment_type}
                onChange={(e) => setFormData({ ...formData, treatment_type: e.target.value as TreatmentType })}
              >
                {TREATMENT_TYPES.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Cycle Number *
              </label>
              <input
                type="number"
                required
                min={1}
                className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                value={formData.cycle_number}
                onChange={(e) => setFormData({ ...formData, cycle_number: parseInt(e.target.value) })}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Start Date *
            </label>
            <input
              type="date"
              required
              className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              value={formData.start_date}
              onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Regimen
            </label>
            <input
              type="text"
              className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              placeholder="e.g., Every 3 weeks, Weekly"
              value={formData.regimen || ''}
              onChange={(e) => setFormData({ ...formData, regimen: e.target.value })}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Dose
            </label>
            <input
              type="text"
              className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              placeholder="e.g., 175 mg/m², 200 mg"
              value={formData.dose || ''}
              onChange={(e) => setFormData({ ...formData, dose: e.target.value })}
            />
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" disabled={isSubmitting}>
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Creating...
                </>
              ) : (
                'Create Cycle'
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
