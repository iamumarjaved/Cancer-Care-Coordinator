'use client';

import { useState, useMemo } from 'react';
import { TreatmentProcedure, TreatmentCycle, ProcedureType, TreatmentProcedureCreate } from '@/types';
import { Card, CardContent, CardHeader, CardTitle, Badge, Button } from '@/components/ui';
import { ProcedureCard } from './ProcedureCard';
import { AddProcedureModal } from './AddProcedureModal';
import { AddTreatmentCycleModal } from './AddTreatmentCycleModal';
import {
  usePatientProcedures,
  useUpcomingProcedures,
  usePatientCalendar,
  useCompleteProcedure,
  useCancelProcedure,
  useCreateProcedure,
  useGenerateProcedures,
} from '@/hooks/useProcedures';
import { useTreatmentCycles, useCreateTreatmentCycle } from '@/hooks/useTreatmentCycles';
import { format, startOfMonth, endOfMonth, eachDayOfInterval, isSameDay, parseISO, addMonths, subMonths } from 'date-fns';
import {
  Calendar,
  List,
  Plus,
  ChevronLeft,
  ChevronRight,
  Loader2,
  AlertCircle,
  CalendarDays,
  Clock,
} from 'lucide-react';

interface ProceduresTabProps {
  patientId: string;
}

type ViewMode = 'list' | 'calendar';

export function ProceduresTab({ patientId }: ProceduresTabProps) {
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [showAddProcedureModal, setShowAddProcedureModal] = useState(false);
  const [showAddCycleModal, setShowAddCycleModal] = useState(false);
  const [selectedCycleId, setSelectedCycleId] = useState<string | null>(null);

  // Fetch data
  const { data: procedures, isLoading: loadingProcedures, error: proceduresError } = usePatientProcedures(patientId);
  const { data: upcomingProcedures } = useUpcomingProcedures(patientId, 7);
  const { data: calendarData } = usePatientCalendar(
    patientId,
    currentMonth.getMonth() + 1,
    currentMonth.getFullYear()
  );
  const { data: treatmentCycles } = useTreatmentCycles(patientId, 'ongoing');

  // Mutations
  const completeProcedure = useCompleteProcedure();
  const cancelProcedure = useCancelProcedure();
  const createProcedure = useCreateProcedure();
  const generateProcedures = useGenerateProcedures();
  const createTreatmentCycle = useCreateTreatmentCycle();

  // Group procedures by status for list view
  const groupedProcedures = useMemo(() => {
    if (!procedures) return { scheduled: [], completed: [], other: [] };

    const scheduled = procedures.filter((p) => p.status === 'scheduled');
    const completed = procedures.filter((p) => p.status === 'completed');
    const other = procedures.filter((p) => p.status === 'missed' || p.status === 'cancelled');

    // Sort scheduled by date ascending, completed by date descending
    scheduled.sort((a, b) => new Date(a.scheduled_date).getTime() - new Date(b.scheduled_date).getTime());
    completed.sort((a, b) => new Date(b.actual_date || b.scheduled_date).getTime() - new Date(a.actual_date || a.scheduled_date).getTime());

    return { scheduled, completed, other };
  }, [procedures]);

  // Calendar helpers
  const calendarDays = useMemo(() => {
    const start = startOfMonth(currentMonth);
    const end = endOfMonth(currentMonth);
    return eachDayOfInterval({ start, end });
  }, [currentMonth]);

  const getProceduresForDay = (day: Date): TreatmentProcedure[] => {
    if (!calendarData) return [];
    const dateKey = format(day, 'yyyy-MM-dd');
    return calendarData[dateKey] || [];
  };

  const handleComplete = async (procedure: TreatmentProcedure) => {
    try {
      await completeProcedure.mutateAsync({
        procedureId: procedure.id,
        cycleId: procedure.treatment_cycle_id,
        patientId: procedure.patient_id,
      });
    } catch (error) {
      console.error('Failed to complete procedure:', error);
    }
  };

  const handleCancel = async (procedure: TreatmentProcedure) => {
    try {
      await cancelProcedure.mutateAsync({
        procedureId: procedure.id,
        cycleId: procedure.treatment_cycle_id,
        patientId: procedure.patient_id,
      });
    } catch (error) {
      console.error('Failed to cancel procedure:', error);
    }
  };

  const handleGenerateSchedule = async (cycleId: string) => {
    try {
      // Default schedule: Day 1, 8, 15 infusions for a 21-day cycle
      await generateProcedures.mutateAsync({
        cycleId,
        patientId,
        params: {
          schedule_days: [1, 8, 15],
          procedure_type: 'infusion',
          start_time: '09:00',
          location: 'Infusion Center',
        },
      });
    } catch (error) {
      console.error('Failed to generate procedures:', error);
    }
  };

  const handleCreateProcedure = async (procedure: TreatmentProcedureCreate) => {
    if (!selectedCycleId) return;
    await createProcedure.mutateAsync({
      cycleId: selectedCycleId,
      procedure,
      patientId,
    });
  };

  const handleCreateTreatmentCycle = async (cycle: Parameters<typeof createTreatmentCycle.mutateAsync>[0]['cycle']) => {
    const newCycle = await createTreatmentCycle.mutateAsync({
      patientId,
      cycle,
    });
    // Auto-select the newly created cycle
    if (newCycle?.id) {
      setSelectedCycleId(newCycle.id);
    }
  };

  // Get the selected cycle details
  const selectedCycle = treatmentCycles?.find((c) => c.id === selectedCycleId);

  if (loadingProcedures) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
      </div>
    );
  }

  if (proceduresError) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardContent className="py-8 text-center">
          <AlertCircle className="w-8 h-8 text-red-500 mx-auto mb-2" />
          <p className="text-red-700">Failed to load procedures</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with view toggle */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Button
            variant={viewMode === 'list' ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setViewMode('list')}
            className="flex items-center gap-1"
          >
            <List className="w-4 h-4" />
            List
          </Button>
          <Button
            variant={viewMode === 'calendar' ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setViewMode('calendar')}
            className="flex items-center gap-1"
          >
            <Calendar className="w-4 h-4" />
            Calendar
          </Button>
        </div>

        <div className="flex items-center gap-2">
          {treatmentCycles && treatmentCycles.length > 0 ? (
            <>
              <select
                className="text-sm border rounded-md px-2 py-1"
                value={selectedCycleId || ''}
                onChange={(e) => setSelectedCycleId(e.target.value || null)}
              >
                <option value="">Select cycle</option>
                {treatmentCycles.map((cycle) => (
                  <option key={cycle.id} value={cycle.id}>
                    {cycle.treatment_name} - Cycle {cycle.cycle_number}
                  </option>
                ))}
              </select>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setShowAddCycleModal(true)}
                title="Add new treatment cycle"
              >
                <Plus className="w-4 h-4" />
              </Button>
            </>
          ) : (
            <Button
              size="sm"
              variant="primary"
              onClick={() => setShowAddCycleModal(true)}
            >
              <Plus className="w-4 h-4 mr-1" />
              Create Treatment Cycle
            </Button>
          )}
            {selectedCycleId && (
              <>
                <Button
                  size="sm"
                  variant="primary"
                  onClick={() => setShowAddProcedureModal(true)}
                  disabled={createProcedure.isPending}
                >
                  <Plus className="w-4 h-4 mr-1" />
                  Add Procedure
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleGenerateSchedule(selectedCycleId)}
                  disabled={generateProcedures.isPending}
                  title="Auto-generate Day 1, 8, 15 infusion schedule"
                >
                  {generateProcedures.isPending ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <CalendarDays className="w-4 h-4 mr-1" />
                  )}
                  Generate Schedule
                </Button>
              </>
            )}
        </div>
      </div>

      {/* Upcoming Procedures Summary */}
      {upcomingProcedures && upcomingProcedures.length > 0 && (
        <Card className="border-primary-200 bg-primary-50/50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Clock className="w-4 h-4" />
              Upcoming (Next 7 Days)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {upcomingProcedures.slice(0, 3).map((procedure) => (
                <ProcedureCard key={procedure.id} procedure={procedure} compact />
              ))}
              {upcomingProcedures.length > 3 && (
                <p className="text-sm text-secondary-500 pl-2">
                  +{upcomingProcedures.length - 3} more scheduled
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* List View */}
      {viewMode === 'list' && (
        <div className="space-y-6">
          {/* Scheduled */}
          {groupedProcedures.scheduled.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-secondary-700 mb-3 flex items-center gap-2">
                <CalendarDays className="w-4 h-4" />
                Scheduled ({groupedProcedures.scheduled.length})
              </h3>
              <div className="space-y-3">
                {groupedProcedures.scheduled.map((procedure) => (
                  <ProcedureCard
                    key={procedure.id}
                    procedure={procedure}
                    onComplete={() => handleComplete(procedure)}
                    onCancel={() => handleCancel(procedure)}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Completed */}
          {groupedProcedures.completed.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-secondary-700 mb-3">
                Completed ({groupedProcedures.completed.length})
              </h3>
              <div className="space-y-3">
                {groupedProcedures.completed.slice(0, 10).map((procedure) => (
                  <ProcedureCard key={procedure.id} procedure={procedure} />
                ))}
              </div>
            </div>
          )}

          {/* Missed/Cancelled */}
          {groupedProcedures.other.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-secondary-700 mb-3">
                Missed/Cancelled ({groupedProcedures.other.length})
              </h3>
              <div className="space-y-3">
                {groupedProcedures.other.map((procedure) => (
                  <ProcedureCard key={procedure.id} procedure={procedure} />
                ))}
              </div>
            </div>
          )}

          {/* Empty State */}
          {procedures?.length === 0 && (
            <Card>
              <CardContent className="py-12 text-center">
                <CalendarDays className="w-12 h-12 text-secondary-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-secondary-900 mb-2">
                  No procedures scheduled
                </h3>
                {treatmentCycles && treatmentCycles.length > 0 ? (
                  <p className="text-secondary-500 mb-4">
                    Select a treatment cycle above to generate a procedure schedule.
                  </p>
                ) : (
                  <>
                    <p className="text-secondary-500 mb-4">
                      Create a treatment cycle first to start scheduling procedures.
                    </p>
                    <Button
                      variant="primary"
                      onClick={() => setShowAddCycleModal(true)}
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Create Treatment Cycle
                    </Button>
                  </>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Calendar View */}
      {viewMode === 'calendar' && (
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentMonth(subMonths(currentMonth, 1))}
              >
                <ChevronLeft className="w-4 h-4" />
              </Button>
              <CardTitle>{format(currentMonth, 'MMMM yyyy')}</CardTitle>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentMonth(addMonths(currentMonth, 1))}
              >
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {/* Day headers */}
            <div className="grid grid-cols-7 gap-1 mb-2">
              {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
                <div key={day} className="text-center text-xs font-medium text-secondary-500 py-2">
                  {day}
                </div>
              ))}
            </div>

            {/* Calendar grid */}
            <div className="grid grid-cols-7 gap-1">
              {/* Empty cells for days before the first of the month */}
              {Array.from({ length: startOfMonth(currentMonth).getDay() }).map((_, i) => (
                <div key={`empty-start-${i}`} className="h-24 bg-secondary-50 rounded-md" />
              ))}

              {/* Days of the month */}
              {calendarDays.map((day) => {
                const dayProcedures = getProceduresForDay(day);
                const isToday = isSameDay(day, new Date());

                return (
                  <div
                    key={day.toISOString()}
                    className={`h-24 p-1 rounded-md border ${
                      isToday ? 'border-primary-300 bg-primary-50' : 'border-secondary-100'
                    }`}
                  >
                    <div className={`text-xs font-medium mb-1 ${isToday ? 'text-primary-700' : 'text-secondary-700'}`}>
                      {format(day, 'd')}
                    </div>
                    <div className="space-y-0.5 overflow-hidden">
                      {dayProcedures.slice(0, 2).map((proc) => (
                        <div
                          key={proc.id}
                          className={`text-xs px-1 py-0.5 rounded truncate ${
                            proc.status === 'completed'
                              ? 'bg-green-100 text-green-700'
                              : proc.status === 'cancelled'
                              ? 'bg-secondary-100 text-secondary-500'
                              : 'bg-blue-100 text-blue-700'
                          }`}
                          title={proc.procedure_name}
                        >
                          {proc.procedure_name}
                        </div>
                      ))}
                      {dayProcedures.length > 2 && (
                        <div className="text-xs text-secondary-500 px-1">
                          +{dayProcedures.length - 2} more
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}

              {/* Empty cells for days after the last of the month */}
              {Array.from({ length: 6 - endOfMonth(currentMonth).getDay() }).map((_, i) => (
                <div key={`empty-end-${i}`} className="h-24 bg-secondary-50 rounded-md" />
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Add Procedure Modal */}
      {selectedCycle && (
        <AddProcedureModal
          isOpen={showAddProcedureModal}
          onClose={() => setShowAddProcedureModal(false)}
          onSubmit={handleCreateProcedure}
          cycleId={selectedCycleId!}
          cycleName={`${selectedCycle.treatment_name} - Cycle ${selectedCycle.cycle_number}`}
          cycleStartDate={selectedCycle.start_date}
        />
      )}

      {/* Add Treatment Cycle Modal */}
      <AddTreatmentCycleModal
        isOpen={showAddCycleModal}
        onClose={() => setShowAddCycleModal(false)}
        onSubmit={handleCreateTreatmentCycle}
        patientId={patientId}
      />
    </div>
  );
}
