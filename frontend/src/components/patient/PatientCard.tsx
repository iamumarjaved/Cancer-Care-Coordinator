'use client';

import { Patient } from '@/types';
import { Card, CardContent, CardHeader, CardTitle, Badge } from '@/components/ui';
import { calculateAge, formatCancerStage } from '@/lib/utils';
import { User, Activity, FileText } from 'lucide-react';
import Link from 'next/link';

interface PatientCardProps {
  patient: Patient;
  showActions?: boolean;
}

export function PatientCard({ patient, showActions = true }: PatientCardProps) {
  const age = calculateAge(patient.date_of_birth);
  const ecogStatus = patient.ecog_status ?? 1;
  const cancerDetails = patient.cancer_details;
  const isClosed = patient.status === 'closed';

  return (
    <Card className={`hover:shadow-md transition-shadow h-full flex flex-col ${isClosed ? 'opacity-60 bg-gray-50' : ''}`}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${isClosed ? 'bg-gray-200' : 'bg-primary-100'}`}>
              <User className={`w-5 h-5 ${isClosed ? 'text-gray-500' : 'text-primary-600'}`} />
            </div>
            <div>
              <CardTitle className="text-base">
                {patient.first_name} {patient.last_name}
              </CardTitle>
              <p className="text-sm text-secondary-500">
                {age} years old • {patient.sex || 'Unknown'}
              </p>
            </div>
          </div>
          {isClosed ? (
            <Badge variant="default" className="bg-gray-200 text-gray-600">Closed</Badge>
          ) : (
            <Badge variant={ecogStatus <= 1 ? 'success' : 'warning'}>
              ECOG {ecogStatus}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="flex-grow flex flex-col">
        <div className="space-y-3 flex-grow">
          {/* Cancer Details */}
          {cancerDetails ? (
            <div className="flex items-center gap-2 text-sm">
              <Activity className="w-4 h-4 text-secondary-400" />
              <span className="text-secondary-700">
                {cancerDetails.cancer_type}
                {cancerDetails.subtype && ` - ${cancerDetails.subtype}`}
              </span>
              {cancerDetails.stage && (
                <Badge variant="info">{formatCancerStage(cancerDetails.stage)}</Badge>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-2 text-sm">
              <Activity className="w-4 h-4 text-secondary-400" />
              <span className="text-secondary-500 italic">Cancer details pending</span>
            </div>
          )}

          {/* Comorbidities */}
          {patient.comorbidities && patient.comorbidities.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {patient.comorbidities.slice(0, 3).map((c, i) => (
                <Badge key={i} variant="default" className="text-xs">
                  {typeof c === 'string' ? c : c.condition}
                </Badge>
              ))}
              {patient.comorbidities.length > 3 && (
                <Badge variant="default" className="text-xs">
                  +{patient.comorbidities.length - 3} more
                </Badge>
              )}
            </div>
          )}

          {/* Genomic Report Status */}
          {patient.genomic_report_id && (
            <div className="flex items-center gap-2 text-sm text-secondary-600">
              <FileText className="w-4 h-4" />
              <span>Genomic report available</span>
            </div>
          )}
        </div>

        {/* Actions - outside content div with mt-auto for bottom alignment */}
        {showActions && (
          <div className="flex gap-2 pt-4 mt-auto">
            <Link
              href={`/patients/${patient.id}`}
              className="flex-1 text-center py-2 text-sm font-medium text-primary-600 hover:bg-primary-50 rounded-md transition-colors"
            >
              View Details
            </Link>
            <Link
              href={`/patients/${patient.id}/analysis`}
              className="flex-1 text-center py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-md transition-colors"
            >
              Run Analysis
            </Link>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
