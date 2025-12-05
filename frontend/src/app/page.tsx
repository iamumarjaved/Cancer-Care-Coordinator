'use client';

import Link from 'next/link';
import { usePatients } from '@/hooks/usePatients';
import { PatientCard } from '@/components/patient/PatientCard';
import { Card, CardContent, Button } from '@/components/ui';
import { Users, Activity, CheckCircle2, FileText, Loader2, TrendingUp, ArrowUpRight, Clock, Stethoscope } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export default function Dashboard() {
  const { data: patientsData, isLoading } = usePatients({ page_size: 6 });

  // Fetch analysis stats with polling every 3 seconds
  const { data: analysisStats } = useQuery({
    queryKey: ['analysis-stats'],
    queryFn: () => api.getAnalysisStats(),
    refetchInterval: 3000,
    staleTime: 1000,
  });

  // Count active patients (not closed)
  const activePatients = patientsData?.items.filter(p => p.status !== 'closed').length || 0;
  const closedPatients = (patientsData?.total || 0) - activePatients;

  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">
            Overview of your cancer care coordination platform
          </p>
        </div>
        <Link href="/patients">
          <Button>
            <Users className="w-4 h-4 mr-2" />
            View All Patients
          </Button>
        </Link>
      </div>

      {/* Enterprise Stats Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {/* Total Patients Card */}
        <Card className="relative overflow-hidden border-0 shadow-md hover:shadow-lg transition-shadow">
          <CardContent className="p-6">
            <div className="flex justify-between items-start">
              <div className="space-y-3">
                <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Total Patients</p>
                <div className="flex items-baseline gap-2">
                  <p className="text-3xl font-bold text-gray-900">{patientsData?.total || 0}</p>
                  {activePatients > 0 && (
                    <span className="text-xs font-medium text-green-600 bg-green-50 px-2 py-0.5 rounded-full">
                      {activePatients} active
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-1 text-sm text-gray-500">
                  <Users className="w-3.5 h-3.5" />
                  <span>{closedPatients} closed cases</span>
                </div>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/25">
                <Users className="w-6 h-6 text-white" />
              </div>
            </div>
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 to-blue-600" />
          </CardContent>
        </Card>

        {/* Active Analyses Card */}
        <Card className="relative overflow-hidden border-0 shadow-md hover:shadow-lg transition-shadow">
          <CardContent className="p-6">
            <div className="flex justify-between items-start">
              <div className="space-y-3">
                <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Active Analyses</p>
                <div className="flex items-baseline gap-2">
                  <p className="text-3xl font-bold text-gray-900">{analysisStats?.active_analyses ?? 0}</p>
                  {(analysisStats?.active_analyses ?? 0) > 0 && (
                    <span className="text-xs font-medium text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full flex items-center gap-1">
                      <Loader2 className="w-3 h-3 animate-spin" />
                      processing
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-1 text-sm text-gray-500">
                  <Clock className="w-3.5 h-3.5" />
                  <span>Real-time status</span>
                </div>
              </div>
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center shadow-lg ${
                (analysisStats?.active_analyses ?? 0) > 0
                  ? 'bg-gradient-to-br from-amber-500 to-orange-500 shadow-amber-500/25'
                  : 'bg-gradient-to-br from-emerald-500 to-green-600 shadow-emerald-500/25'
              }`}>
                {(analysisStats?.active_analyses ?? 0) > 0 ? (
                  <Activity className="w-6 h-6 text-white animate-pulse" />
                ) : (
                  <CheckCircle2 className="w-6 h-6 text-white" />
                )}
              </div>
            </div>
            <div className={`absolute bottom-0 left-0 right-0 h-1 ${
              (analysisStats?.active_analyses ?? 0) > 0
                ? 'bg-gradient-to-r from-amber-500 to-orange-500'
                : 'bg-gradient-to-r from-emerald-500 to-green-600'
            }`} />
          </CardContent>
        </Card>

        {/* AI Analyses Card */}
        <Card className="relative overflow-hidden border-0 shadow-md hover:shadow-lg transition-shadow">
          <CardContent className="p-6">
            <div className="flex justify-between items-start">
              <div className="space-y-3">
                <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">AI Analyses</p>
                <div className="flex items-baseline gap-2">
                  <p className="text-3xl font-bold text-gray-900">{analysisStats?.completed_today ?? 0}</p>
                  {(analysisStats?.completed_today ?? 0) > 0 && (
                    <span className="text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" />
                      completed
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-1 text-sm text-gray-500">
                  <TrendingUp className="w-3.5 h-3.5" />
                  <span>Treatment plans generated</span>
                </div>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-purple-500/25">
                <TrendingUp className="w-6 h-6 text-white" />
              </div>
            </div>
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-purple-500 to-purple-600" />
          </CardContent>
        </Card>

        {/* Clinical Notes Card */}
        <Card className="relative overflow-hidden border-0 shadow-md hover:shadow-lg transition-shadow">
          <CardContent className="p-6">
            <div className="flex justify-between items-start">
              <div className="space-y-3">
                <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Clinical Notes</p>
                <div className="flex items-baseline gap-2">
                  <p className="text-3xl font-bold text-gray-900">{analysisStats?.clinical_notes_count ?? 0}</p>
                  <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
                    total
                  </span>
                </div>
                <div className="flex items-center gap-1 text-sm text-gray-500">
                  <Stethoscope className="w-3.5 h-3.5" />
                  <span>Doctor updates recorded</span>
                </div>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-pink-500 to-rose-500 rounded-xl flex items-center justify-center shadow-lg shadow-pink-500/25">
                <FileText className="w-6 h-6 text-white" />
              </div>
            </div>
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-pink-500 to-rose-500" />
          </CardContent>
        </Card>
      </div>

      {/* Recent Patients */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Recent Patients</h2>
            <p className="text-sm text-gray-500">Quick access to your latest patient files</p>
          </div>
          <Link href="/patients">
            <Button variant="outline" size="sm" className="group">
              View All
              <ArrowUpRight className="w-4 h-4 ml-1 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
            </Button>
          </Link>
        </div>

        {isLoading ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <Card key={i} className="animate-pulse border-0 shadow-md">
                <CardContent className="p-6 h-48">
                  <div className="h-4 bg-gray-200 rounded w-3/4 mb-4" />
                  <div className="h-3 bg-gray-200 rounded w-1/2 mb-2" />
                  <div className="h-3 bg-gray-200 rounded w-2/3" />
                </CardContent>
              </Card>
            ))}
          </div>
        ) : patientsData?.items.length === 0 ? (
          <Card className="border-0 shadow-md">
            <CardContent className="p-12 text-center">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Users className="w-8 h-8 text-gray-400" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No patients yet</h3>
              <p className="text-gray-500 mb-4">Get started by adding your first patient</p>
              <Link href="/patients">
                <Button>Add Patient</Button>
              </Link>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {patientsData?.items.map((patient) => (
              <PatientCard key={patient.id} patient={patient} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
