'use client';

import { useState } from 'react';
import { usePatients } from '@/hooks/usePatients';
import { PatientCard } from '@/components/patient/PatientCard';
import { AddPatientModal } from '@/components/patient/AddPatientModal';
import { Card, CardContent, Button, Badge } from '@/components/ui';
import { Search, Filter, Users, Database, Trash2, Loader2, CheckCircle, Plus } from 'lucide-react';
import api from '@/lib/api';

export default function PatientsPage() {
  const [search, setSearch] = useState('');
  const [cancerType, setCancerType] = useState<string | undefined>();
  const [page, setPage] = useState(1);
  const [isPopulating, setIsPopulating] = useState(false);
  const [isClearing, setIsClearing] = useState(false);
  const [populateMessage, setPopulateMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [isAddPatientModalOpen, setIsAddPatientModalOpen] = useState(false);

  const { data, isLoading, error, refetch } = usePatients({
    page,
    page_size: 12,
    search: search || undefined,
    cancer_type: cancerType,
  });

  const cancerTypes = ['NSCLC', 'SCLC', 'Breast', 'Colorectal', 'Melanoma', 'Pancreatic'];

  const handlePopulateTestData = async () => {
    setIsPopulating(true);
    setPopulateMessage(null);
    try {
      const result = await api.populateTestData();
      setPopulateMessage({
        type: 'success',
        text: `Created ${result.patients_created} test patients`,
      });
      refetch();
    } catch (err) {
      setPopulateMessage({
        type: 'error',
        text: err instanceof Error ? err.message : 'Failed to populate test data',
      });
    } finally {
      setIsPopulating(false);
      setTimeout(() => setPopulateMessage(null), 5000);
    }
  };

  const handleClearTestData = async () => {
    if (!confirm('Are you sure you want to delete all test patients?')) return;
    setIsClearing(true);
    setPopulateMessage(null);
    try {
      const result = await api.clearTestData();
      setPopulateMessage({
        type: 'success',
        text: `Deleted ${result.patients_deleted} test patients`,
      });
      refetch();
    } catch (err) {
      setPopulateMessage({
        type: 'error',
        text: err instanceof Error ? err.message : 'Failed to clear test data',
      });
    } finally {
      setIsClearing(false);
      setTimeout(() => setPopulateMessage(null), 5000);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Patients</h1>
          <p className="text-gray-600 mt-1">Manage and analyze patient cases</p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="info">
            <Users className="w-3 h-3 mr-1" />
            {data?.total || 0} patients
          </Badge>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsAddPatientModalOpen(true)}
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Patient
          </Button>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handlePopulateTestData}
              disabled={isPopulating || isClearing}
            >
              {isPopulating ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Database className="w-4 h-4 mr-2" />
              )}
              {isPopulating ? 'Populating...' : 'Load Test Data'}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClearTestData}
              disabled={isPopulating || isClearing}
              className="text-red-600 hover:text-red-700 hover:bg-red-50"
            >
              {isClearing ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Trash2 className="w-4 h-4 mr-2" />
              )}
              {isClearing ? 'Clearing...' : 'Clear Test Data'}
            </Button>
          </div>
        </div>
      </div>

      {/* Feedback Message */}
      {populateMessage && (
        <div
          className={`flex items-center gap-2 px-4 py-3 rounded-lg ${
            populateMessage.type === 'success'
              ? 'bg-green-50 text-green-800 border border-green-200'
              : 'bg-red-50 text-red-800 border border-red-200'
          }`}
        >
          {populateMessage.type === 'success' ? (
            <CheckCircle className="w-5 h-5" />
          ) : (
            <span className="text-red-500">⚠</span>
          )}
          <span>{populateMessage.text}</span>
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col md:flex-row gap-4">
            {/* Search */}
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search patients..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(1);
                }}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>

            {/* Cancer Type Filter */}
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-gray-400" />
              <div className="flex flex-wrap gap-2">
                <Button
                  variant={cancerType === undefined ? 'primary' : 'outline'}
                  size="sm"
                  onClick={() => {
                    setCancerType(undefined);
                    setPage(1);
                  }}
                >
                  All
                </Button>
                {cancerTypes.map((type) => (
                  <Button
                    key={type}
                    variant={cancerType === type ? 'primary' : 'outline'}
                    size="sm"
                    onClick={() => {
                      setCancerType(type);
                      setPage(1);
                    }}
                  >
                    {type}
                  </Button>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Patient Grid */}
      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="p-6 h-48">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-4" />
                <div className="h-3 bg-gray-200 rounded w-1/2 mb-2" />
                <div className="h-3 bg-gray-200 rounded w-2/3" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : error ? (
        <Card>
          <CardContent className="p-6 text-center">
            <p className="text-red-600">Error loading patients: {(error as Error).message}</p>
          </CardContent>
        </Card>
      ) : data?.items.length === 0 ? (
        <Card>
          <CardContent className="p-6 text-center">
            <Users className="w-12 h-12 mx-auto text-gray-300 mb-4" />
            <p className="text-gray-500">No patients found</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {data?.items.map((patient) => (
            <PatientCard key={patient.id} patient={patient} />
          ))}
        </div>
      )}

      {/* Pagination */}
      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
          >
            Previous
          </Button>
          <span className="text-sm text-gray-600">
            Page {page} of {data.total_pages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= data.total_pages}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </Button>
        </div>
      )}

      {/* Add Patient Modal */}
      <AddPatientModal
        isOpen={isAddPatientModalOpen}
        onClose={() => setIsAddPatientModalOpen(false)}
        onSuccess={() => {
          setIsAddPatientModalOpen(false);
          refetch();
        }}
      />
    </div>
  );
}
