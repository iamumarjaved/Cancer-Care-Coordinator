'use client';

import { useState, useEffect, useRef } from 'react';
import { Button, Card, CardContent, CardHeader, CardTitle, Badge } from '@/components/ui';
import { X, ChevronLeft, ChevronRight, User, Stethoscope, FileText, Loader2, Wand2 } from 'lucide-react';
import { useCreatePatient } from '@/hooks/usePatients';

// Test data templates for different cancer scenarios
const TEST_DATA_TEMPLATES: Record<string, FormData> = {
  // EGFR-mutant NSCLC - Best for demonstrating targeted therapy recommendations
  'EGFR NSCLC': {
    first_name: 'Michael',
    last_name: 'Chen',
    date_of_birth: '1962-03-15',
    sex: 'Male',
    email: 'michael.chen@email.com',
    phone: '(555) 234-5678',
    cancer_type: 'NSCLC',
    cancer_subtype: 'Adenocarcinoma, EGFR exon 19 deletion',
    stage: 'Stage IV',
    diagnosis_date: '2024-09-15',
    primary_site: 'Right upper lobe',
    metastases: ['Brain', 'Bone'],
    ecog_status: 1,
    comorbidities: ['Hypertension', 'Type 2 Diabetes'],
    current_medications: 'Metformin 1000mg BID, Lisinopril 10mg daily, Aspirin 81mg daily',
    allergies: 'Sulfa drugs',
    smoking_status: 'Former',
    pack_years: '30',
    insurance_provider: 'Blue Cross Blue Shield',
  },
  // ALK-positive NSCLC - For demonstrating ALK inhibitor recommendations
  'ALK NSCLC': {
    first_name: 'Sarah',
    last_name: 'Johnson',
    date_of_birth: '1975-07-22',
    sex: 'Female',
    email: 'sarah.johnson@email.com',
    phone: '(555) 345-6789',
    cancer_type: 'NSCLC',
    cancer_subtype: 'Adenocarcinoma, ALK-rearranged',
    stage: 'Stage IV',
    diagnosis_date: '2024-08-01',
    primary_site: 'Left lower lobe',
    metastases: ['Brain', 'Liver'],
    ecog_status: 1,
    comorbidities: [],
    current_medications: 'Multivitamin daily, Calcium + Vitamin D',
    allergies: '',
    smoking_status: 'Never',
    pack_years: '',
    insurance_provider: 'Aetna',
  },
  // KRAS G12C NSCLC with high PD-L1 - For immunotherapy + targeted therapy
  'KRAS Immunotherapy': {
    first_name: 'William',
    last_name: 'Martinez',
    date_of_birth: '1958-11-08',
    sex: 'Male',
    email: 'william.martinez@email.com',
    phone: '(555) 456-7890',
    cancer_type: 'NSCLC',
    cancer_subtype: 'Adenocarcinoma, KRAS G12C, PD-L1 80%',
    stage: 'Stage IV',
    diagnosis_date: '2024-10-01',
    primary_site: 'Right middle lobe',
    metastases: ['Adrenal', 'Lymph nodes'],
    ecog_status: 0,
    comorbidities: ['COPD', 'Hypertension'],
    current_medications: 'Tiotropium inhaler, Amlodipine 5mg daily',
    allergies: 'Penicillin',
    smoking_status: 'Former',
    pack_years: '45',
    insurance_provider: 'Medicare',
  },
  // HER2+ Breast Cancer
  'HER2 Breast': {
    first_name: 'Jennifer',
    last_name: 'Williams',
    date_of_birth: '1968-04-12',
    sex: 'Female',
    email: 'jennifer.williams@email.com',
    phone: '(555) 567-8901',
    cancer_type: 'Breast',
    cancer_subtype: 'Invasive ductal carcinoma, HER2-positive, ER/PR-negative',
    stage: 'Stage IV',
    diagnosis_date: '2024-07-20',
    primary_site: 'Left breast',
    metastases: ['Liver', 'Bone'],
    ecog_status: 1,
    comorbidities: ['Hypothyroidism'],
    current_medications: 'Levothyroxine 75mcg daily',
    allergies: '',
    smoking_status: 'Never',
    pack_years: '',
    insurance_provider: 'UnitedHealthcare',
  },
  // MSI-H Colorectal - For immunotherapy
  'MSI-H Colorectal': {
    first_name: 'Lisa',
    last_name: 'Taylor',
    date_of_birth: '1970-09-25',
    sex: 'Female',
    email: 'lisa.taylor@email.com',
    phone: '(555) 678-9012',
    cancer_type: 'Colorectal',
    cancer_subtype: 'Adenocarcinoma, MSI-High, Lynch syndrome',
    stage: 'Stage IIIB',
    diagnosis_date: '2024-06-15',
    primary_site: 'Ascending colon',
    metastases: ['Lymph nodes'],
    ecog_status: 0,
    comorbidities: [],
    current_medications: 'Iron supplements, Vitamin B12',
    allergies: 'Iodine contrast',
    smoking_status: 'Never',
    pack_years: '',
    insurance_provider: 'Cigna',
  },
};

interface AddPatientModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

const CANCER_TYPES = ['NSCLC', 'SCLC', 'Breast', 'Colorectal', 'Melanoma', 'Pancreatic', 'Other'];
const STAGES = ['Stage I', 'Stage II', 'Stage IIIA', 'Stage IIIB', 'Stage IIIC', 'Stage IV'];
const ECOG_STATUS = [
  { value: 0, label: '0 - Fully active' },
  { value: 1, label: '1 - Restricted but ambulatory' },
  { value: 2, label: '2 - Ambulatory, self-care capable' },
  { value: 3, label: '3 - Limited self-care' },
  { value: 4, label: '4 - Completely disabled' },
];
const COMMON_COMORBIDITIES = [
  'Hypertension',
  'Type 2 Diabetes',
  'COPD',
  'Chronic Kidney Disease',
  'Heart Failure',
  'Coronary Artery Disease',
  'Atrial Fibrillation',
  'Hypothyroidism',
];

interface FormData {
  // Basic Info (Step 1)
  first_name: string;
  last_name: string;
  date_of_birth: string;
  sex: string;
  email: string;
  phone: string;
  // Cancer Info (Step 2)
  cancer_type: string;
  cancer_subtype: string;
  stage: string;
  diagnosis_date: string;
  primary_site: string;
  metastases: string[];
  ecog_status: number | null;
  // Medical History (Step 3)
  comorbidities: string[];
  current_medications: string;
  allergies: string;
  smoking_status: string;
  pack_years: string;
  insurance_provider: string;
}

const initialFormData: FormData = {
  first_name: '',
  last_name: '',
  date_of_birth: '',
  sex: '',
  email: '',
  phone: '',
  cancer_type: '',
  cancer_subtype: '',
  stage: '',
  diagnosis_date: '',
  primary_site: '',
  metastases: [],
  ecog_status: null,
  comorbidities: [],
  current_medications: '',
  allergies: '',
  smoking_status: '',
  pack_years: '',
  insurance_provider: '',
};

export function AddPatientModal({ isOpen, onClose, onSuccess }: AddPatientModalProps) {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState<FormData>(initialFormData);
  const [error, setError] = useState<string | null>(null);
  const [showTestDataMenu, setShowTestDataMenu] = useState(false);
  const testDataMenuRef = useRef<HTMLDivElement>(null);

  const createPatient = useCreatePatient();

  // Close test data menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (testDataMenuRef.current && !testDataMenuRef.current.contains(event.target as Node)) {
        setShowTestDataMenu(false);
      }
    };
    if (showTestDataMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showTestDataMenu]);

  const updateForm = (field: keyof FormData, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const populateTestData = (templateName: string) => {
    const template = TEST_DATA_TEMPLATES[templateName];
    if (template) {
      setFormData({ ...template });
      setShowTestDataMenu(false);
      setStep(1); // Go back to first step to review
    }
  };

  const toggleArrayItem = (field: 'comorbidities' | 'metastases', item: string) => {
    setFormData((prev) => ({
      ...prev,
      [field]: prev[field].includes(item)
        ? prev[field].filter((i) => i !== item)
        : [...prev[field], item],
    }));
  };

  const handleSubmit = async () => {
    setError(null);
    try {
      // Build patient data
      const patientData = {
        id: `P${Date.now()}`,
        first_name: formData.first_name,
        last_name: formData.last_name,
        date_of_birth: formData.date_of_birth,
        sex: formData.sex || 'Unknown',
        email: formData.email || undefined,
        phone: formData.phone || undefined,
        cancer_details: {
          cancer_type: formData.cancer_type,
          subtype: formData.cancer_subtype || undefined,
          stage: formData.stage,
          primary_site: formData.primary_site || undefined,
          metastases: formData.metastases,
          diagnosis_date: formData.diagnosis_date || undefined,
        },
        comorbidities: formData.comorbidities.map((c) => ({
          condition: c,
          severity: 'moderate',
          treatment_implications: [],
        })),
        organ_function: [],
        ecog_status: formData.ecog_status ?? 1,
        current_medications: formData.current_medications
          ? formData.current_medications.split(',').map((m) => m.trim())
          : [],
        allergies: formData.allergies
          ? formData.allergies.split(',').map((a) => a.trim())
          : [],
        smoking_status: formData.smoking_status || undefined,
        pack_years: formData.pack_years ? parseInt(formData.pack_years) : undefined,
      };

      await createPatient.mutateAsync(patientData);
      setFormData(initialFormData);
      setStep(1);
      onSuccess?.();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create patient');
    }
  };

  const canProceed = () => {
    if (step === 1) {
      return formData.first_name && formData.last_name && formData.date_of_birth;
    }
    if (step === 2) {
      return formData.cancer_type && formData.stage;
    }
    return true;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      {/* Modal */}
      <div className="relative w-full max-w-2xl max-h-[90vh] overflow-auto bg-white rounded-xl shadow-2xl mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Add New Patient</h2>
            <p className="text-sm text-gray-500 mt-1">Step {step} of 3</p>
          </div>
          <div className="flex items-center gap-2">
            {/* Populate Test Data Button */}
            <div className="relative" ref={testDataMenuRef}>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowTestDataMenu(!showTestDataMenu)}
                className="text-purple-600 border-purple-300 hover:bg-purple-50"
              >
                <Wand2 className="w-4 h-4 mr-1" />
                Test Data
              </Button>
              {showTestDataMenu && (
                <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
                  <div className="p-2">
                    <p className="text-xs font-medium text-gray-500 px-2 py-1">
                      Select a test scenario:
                    </p>
                    {Object.keys(TEST_DATA_TEMPLATES).map((templateName) => (
                      <button
                        key={templateName}
                        onClick={() => populateTestData(templateName)}
                        className="w-full text-left px-3 py-2 text-sm hover:bg-purple-50 rounded-md transition-colors"
                      >
                        <span className="font-medium text-gray-900">{templateName}</span>
                        <p className="text-xs text-gray-500 mt-0.5">
                          {templateName.includes('EGFR') && 'Targeted therapy (Osimertinib)'}
                          {templateName.includes('ALK') && 'ALK inhibitors (Alectinib)'}
                          {templateName.includes('KRAS') && 'Immunotherapy + Sotorasib'}
                          {templateName.includes('HER2') && 'HER2-targeted therapy'}
                          {templateName.includes('MSI') && 'Immunotherapy candidate'}
                        </p>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>
        </div>

        {/* Progress Steps */}
        <div className="flex items-center gap-2 px-6 py-4 bg-gray-50 border-b">
          {[
            { num: 1, label: 'Basic Info', icon: User },
            { num: 2, label: 'Cancer Info', icon: Stethoscope },
            { num: 3, label: 'Medical History', icon: FileText },
          ].map(({ num, label, icon: Icon }) => (
            <div
              key={num}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg flex-1 ${
                step === num
                  ? 'bg-primary-100 text-primary-700'
                  : step > num
                  ? 'bg-green-100 text-green-700'
                  : 'bg-gray-100 text-gray-500'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span className="text-sm font-medium">{label}</span>
            </div>
          ))}
        </div>

        {/* Form Content */}
        <div className="p-6 space-y-6">
          {/* Step 1: Basic Info */}
          {step === 1 && (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    First Name *
                  </label>
                  <input
                    type="text"
                    value={formData.first_name}
                    onChange={(e) => updateForm('first_name', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="John"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Last Name *
                  </label>
                  <input
                    type="text"
                    value={formData.last_name}
                    onChange={(e) => updateForm('last_name', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="Doe"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Date of Birth *
                  </label>
                  <input
                    type="date"
                    value={formData.date_of_birth}
                    onChange={(e) => updateForm('date_of_birth', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Sex</label>
                  <select
                    value={formData.sex}
                    onChange={(e) => updateForm('sex', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">Select...</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => updateForm('email', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="patient@example.com"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => updateForm('phone', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="(555) 123-4567"
                  />
                </div>
              </div>
            </>
          )}

          {/* Step 2: Cancer Info */}
          {step === 2 && (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Cancer Type *
                  </label>
                  <select
                    value={formData.cancer_type}
                    onChange={(e) => updateForm('cancer_type', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">Select...</option>
                    {CANCER_TYPES.map((type) => (
                      <option key={type} value={type}>
                        {type}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Cancer Subtype
                  </label>
                  <input
                    type="text"
                    value={formData.cancer_subtype}
                    onChange={(e) => updateForm('cancer_subtype', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="e.g., Adenocarcinoma"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Stage *</label>
                  <select
                    value={formData.stage}
                    onChange={(e) => updateForm('stage', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">Select...</option>
                    {STAGES.map((stage) => (
                      <option key={stage} value={stage}>
                        {stage}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Diagnosis Date
                  </label>
                  <input
                    type="date"
                    value={formData.diagnosis_date}
                    onChange={(e) => updateForm('diagnosis_date', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Primary Site
                </label>
                <input
                  type="text"
                  value={formData.primary_site}
                  onChange={(e) => updateForm('primary_site', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="e.g., Right upper lobe"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Metastatic Sites
                </label>
                <div className="flex flex-wrap gap-2">
                  {['Brain', 'Bone', 'Liver', 'Adrenal', 'Lymph nodes', 'Lung (contralateral)', 'Pleura'].map(
                    (site) => (
                      <button
                        key={site}
                        type="button"
                        onClick={() => toggleArrayItem('metastases', site)}
                        className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                          formData.metastases.includes(site)
                            ? 'bg-primary-100 text-primary-700 border-2 border-primary-500'
                            : 'bg-gray-100 text-gray-600 border-2 border-transparent'
                        }`}
                      >
                        {site}
                      </button>
                    )
                  )}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  ECOG Performance Status
                </label>
                <select
                  value={formData.ecog_status ?? ''}
                  onChange={(e) =>
                    updateForm('ecog_status', e.target.value ? parseInt(e.target.value) : null)
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="">Select...</option>
                  {ECOG_STATUS.map(({ value, label }) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>
            </>
          )}

          {/* Step 3: Medical History */}
          {step === 3 && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Comorbidities
                </label>
                <div className="flex flex-wrap gap-2">
                  {COMMON_COMORBIDITIES.map((comorb) => (
                    <button
                      key={comorb}
                      type="button"
                      onClick={() => toggleArrayItem('comorbidities', comorb)}
                      className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                        formData.comorbidities.includes(comorb)
                          ? 'bg-primary-100 text-primary-700 border-2 border-primary-500'
                          : 'bg-gray-100 text-gray-600 border-2 border-transparent'
                      }`}
                    >
                      {comorb}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Current Medications
                </label>
                <textarea
                  value={formData.current_medications}
                  onChange={(e) => updateForm('current_medications', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  rows={2}
                  placeholder="Enter medications, separated by commas"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Allergies</label>
                <input
                  type="text"
                  value={formData.allergies}
                  onChange={(e) => updateForm('allergies', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="Enter allergies, separated by commas"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Smoking Status
                  </label>
                  <select
                    value={formData.smoking_status}
                    onChange={(e) => updateForm('smoking_status', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">Select...</option>
                    <option value="Never">Never smoker</option>
                    <option value="Former">Former smoker</option>
                    <option value="Current">Current smoker</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Pack Years
                  </label>
                  <input
                    type="number"
                    value={formData.pack_years}
                    onChange={(e) => updateForm('pack_years', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="0"
                    min="0"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Insurance Provider
                </label>
                <input
                  type="text"
                  value={formData.insurance_provider}
                  onChange={(e) => updateForm('insurance_provider', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="e.g., Blue Cross Blue Shield"
                />
              </div>
            </>
          )}

          {/* Error Message */}
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t bg-gray-50">
          <Button
            variant="outline"
            onClick={() => setStep((s) => s - 1)}
            disabled={step === 1}
          >
            <ChevronLeft className="w-4 h-4 mr-1" />
            Back
          </Button>

          <div className="flex gap-2">
            <Button variant="ghost" onClick={onClose}>
              Cancel
            </Button>
            {step < 3 ? (
              <Button onClick={() => setStep((s) => s + 1)} disabled={!canProceed()}>
                Next
                <ChevronRight className="w-4 h-4 ml-1" />
              </Button>
            ) : (
              <Button
                onClick={handleSubmit}
                disabled={createPatient.isPending}
              >
                {createPatient.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Creating...
                  </>
                ) : (
                  'Create Patient'
                )}
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
