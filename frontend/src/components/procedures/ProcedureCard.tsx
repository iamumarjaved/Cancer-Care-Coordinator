'use client';

import { TreatmentProcedure, ProcedureStatus, ProcedureType } from '@/types';
import { Card, CardContent, Badge, Button } from '@/components/ui';
import { format, parseISO } from 'date-fns';
import {
  Syringe,
  FlaskConical,
  ScanLine,
  Pill,
  Radiation,
  Stethoscope,
  Circle,
  Check,
  X,
  Clock,
  AlertTriangle,
  MapPin,
} from 'lucide-react';

interface ProcedureCardProps {
  procedure: TreatmentProcedure;
  onComplete?: () => void;
  onCancel?: () => void;
  compact?: boolean;
}

const statusConfig: Record<ProcedureStatus, { label: string; variant: 'default' | 'success' | 'warning' | 'danger' | 'info' }> = {
  scheduled: { label: 'Scheduled', variant: 'info' },
  completed: { label: 'Completed', variant: 'success' },
  missed: { label: 'Missed', variant: 'danger' },
  cancelled: { label: 'Cancelled', variant: 'default' },
};

const procedureIcons: Record<ProcedureType, React.ElementType> = {
  infusion: Syringe,
  lab_check: FlaskConical,
  imaging: ScanLine,
  injection: Syringe,
  oral_medication: Pill,
  radiation_session: Radiation,
  consultation: Stethoscope,
  other: Circle,
};

export function ProcedureCard({
  procedure,
  onComplete,
  onCancel,
  compact = false,
}: ProcedureCardProps) {
  const Icon = procedureIcons[procedure.procedure_type as ProcedureType] || Circle;
  const statusInfo = statusConfig[procedure.status as ProcedureStatus];
  const scheduledDate = parseISO(procedure.scheduled_date);
  const isUpcoming = procedure.status === 'scheduled' && scheduledDate > new Date();
  const isToday =
    procedure.status === 'scheduled' &&
    format(scheduledDate, 'yyyy-MM-dd') === format(new Date(), 'yyyy-MM-dd');

  if (compact) {
    return (
      <div className="flex items-center gap-3 p-2 rounded-lg hover:bg-secondary-50 transition-colors">
        <div className={`p-2 rounded-lg ${isToday ? 'bg-primary-100' : 'bg-secondary-100'}`}>
          <Icon className={`w-4 h-4 ${isToday ? 'text-primary-600' : 'text-secondary-600'}`} />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-secondary-900 truncate">
            {procedure.procedure_name}
          </p>
          <p className="text-xs text-secondary-500">
            {procedure.scheduled_time || format(scheduledDate, 'h:mm a')}
            {procedure.location && ` - ${procedure.location}`}
          </p>
        </div>
        <Badge variant={statusInfo.variant} className="text-xs">
          {statusInfo.label}
        </Badge>
      </div>
    );
  }

  return (
    <Card className={`${isToday ? 'border-primary-200 bg-primary-50/30' : ''}`}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            <div className={`p-2.5 rounded-lg ${isToday ? 'bg-primary-100' : 'bg-secondary-100'}`}>
              <Icon className={`w-5 h-5 ${isToday ? 'text-primary-600' : 'text-secondary-600'}`} />
            </div>
            <div>
              <h3 className="font-medium text-secondary-900">{procedure.procedure_name}</h3>
              <p className="text-sm text-secondary-500 capitalize">
                {procedure.procedure_type.replace('_', ' ')} - Day {procedure.day_number}
              </p>
            </div>
          </div>
          <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>
        </div>

        <div className="mt-4 space-y-2">
          <div className="flex items-center gap-2 text-sm text-secondary-600">
            <Clock className="w-4 h-4" />
            <span>
              {format(scheduledDate, 'MMM d, yyyy')}
              {procedure.scheduled_time && ` at ${procedure.scheduled_time}`}
            </span>
          </div>

          {procedure.location && (
            <div className="flex items-center gap-2 text-sm text-secondary-600">
              <MapPin className="w-4 h-4" />
              <span>{procedure.location}</span>
            </div>
          )}

          {procedure.status === 'completed' && procedure.actual_dose && (
            <div className="flex items-center gap-2 text-sm text-secondary-600">
              <Check className="w-4 h-4 text-green-500" />
              <span>Dose: {procedure.actual_dose}</span>
            </div>
          )}

          {procedure.adverse_events && procedure.adverse_events.length > 0 && (
            <div className="flex items-start gap-2 text-sm text-amber-600">
              <AlertTriangle className="w-4 h-4 mt-0.5" />
              <div>
                <span className="font-medium">Adverse Events:</span>
                <ul className="mt-1 space-y-1">
                  {procedure.adverse_events.map((ae, i) => (
                    <li key={i}>
                      {ae.event}
                      {ae.grade && ` (Grade ${ae.grade})`}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {procedure.administration_notes && (
            <p className="text-sm text-secondary-600 italic mt-2">
              {procedure.administration_notes}
            </p>
          )}
        </div>

        {procedure.status === 'scheduled' && (onComplete || onCancel) && (
          <div className="flex gap-2 mt-4 pt-4 border-t">
            {onComplete && (
              <Button
                size="sm"
                variant="primary"
                onClick={onComplete}
                className="flex items-center gap-1"
              >
                <Check className="w-4 h-4" />
                Complete
              </Button>
            )}
            {onCancel && (
              <Button
                size="sm"
                variant="outline"
                onClick={onCancel}
                className="flex items-center gap-1"
              >
                <X className="w-4 h-4" />
                Cancel
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
