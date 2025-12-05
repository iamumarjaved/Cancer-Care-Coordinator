'use client';

import { ClinicalTrial } from '@/types';
import { Card, CardContent, CardHeader, CardTitle, Badge } from '@/components/ui';
import { formatPercentage, getStatusColor } from '@/lib/utils';
import { MapPin, ExternalLink, CheckCircle, XCircle, HelpCircle } from 'lucide-react';

interface ClinicalTrialCardProps {
  trial: ClinicalTrial;
}

export function ClinicalTrialCard({ trial }: ClinicalTrialCardProps) {
  const eligibilityMet = trial.eligibility_criteria.filter((c) => c.patient_meets === true).length;
  const eligibilityNotMet = trial.eligibility_criteria.filter((c) => c.patient_meets === false).length;
  const eligibilityUnknown = trial.eligibility_criteria.filter((c) => c.patient_meets === null).length;

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="info">{trial.phase}</Badge>
              <Badge className={getStatusColor(trial.status)}>{trial.status}</Badge>
            </div>
            <CardTitle className="text-base">{trial.title}</CardTitle>
            <p className="text-sm text-secondary-500 mt-1">{trial.nct_id}</p>
          </div>
          <div className="text-right">
            <div className="text-lg font-semibold text-primary-600">
              {formatPercentage(trial.match_score)}
            </div>
            <p className="text-xs text-secondary-500">Match Score</p>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Sponsor */}
        {trial.sponsor && (
          <div>
            <p className="text-xs text-secondary-500 uppercase tracking-wide mb-1">Sponsor</p>
            <p className="text-sm text-secondary-700">{trial.sponsor}</p>
          </div>
        )}

        {/* Interventions */}
        {trial.interventions.length > 0 && (
          <div>
            <p className="text-xs text-secondary-500 uppercase tracking-wide mb-1">Interventions</p>
            <div className="flex flex-wrap gap-1">
              {trial.interventions.map((intervention, index) => (
                <Badge key={index} variant="info" className="text-xs">
                  {intervention}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Eligibility Summary */}
        <div>
          <p className="text-xs text-secondary-500 uppercase tracking-wide mb-2">Eligibility Criteria</p>
          <div className="flex gap-4 text-sm">
            <div className="flex items-center gap-1 text-success-600">
              <CheckCircle className="w-4 h-4" />
              <span>{eligibilityMet} met</span>
            </div>
            <div className="flex items-center gap-1 text-danger-600">
              <XCircle className="w-4 h-4" />
              <span>{eligibilityNotMet} not met</span>
            </div>
            <div className="flex items-center gap-1 text-secondary-500">
              <HelpCircle className="w-4 h-4" />
              <span>{eligibilityUnknown} unknown</span>
            </div>
          </div>
        </div>

        {/* Eligibility Details */}
        {trial.eligibility_criteria.length > 0 && (
          <div className="space-y-1">
            {trial.eligibility_criteria.slice(0, 4).map((criterion, index) => (
              <div key={index} className="flex items-start gap-2 text-sm">
                {criterion.patient_meets === true && (
                  <CheckCircle className="w-4 h-4 text-success-500 mt-0.5" />
                )}
                {criterion.patient_meets === false && (
                  <XCircle className="w-4 h-4 text-danger-500 mt-0.5" />
                )}
                {criterion.patient_meets === null && (
                  <HelpCircle className="w-4 h-4 text-secondary-400 mt-0.5" />
                )}
                <div>
                  <span className="text-secondary-700">{criterion.criterion}</span>
                  {criterion.details && (
                    <p className="text-xs text-secondary-500">{criterion.details}</p>
                  )}
                </div>
              </div>
            ))}
            {trial.eligibility_criteria.length > 4 && (
              <p className="text-xs text-secondary-500">
                +{trial.eligibility_criteria.length - 4} more criteria
              </p>
            )}
          </div>
        )}

        {/* Locations */}
        {trial.locations.length > 0 && (
          <div>
            <div className="flex items-center gap-1 mb-1">
              <MapPin className="w-3 h-3 text-secondary-400" />
              <p className="text-xs text-secondary-500 uppercase tracking-wide">Locations</p>
            </div>
            <p className="text-sm text-secondary-600">{trial.locations.slice(0, 2).join('; ')}</p>
            {trial.locations.length > 2 && (
              <p className="text-xs text-secondary-500">+{trial.locations.length - 2} more</p>
            )}
          </div>
        )}

        {/* Match Rationale */}
        {trial.match_rationale && (
          <div className="pt-2 border-t border-secondary-100">
            <p className="text-sm text-secondary-600 italic">{trial.match_rationale}</p>
          </div>
        )}

        {/* ClinicalTrials.gov Link */}
        <a
          href={`https://clinicaltrials.gov/study/${trial.nct_id}`}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-sm text-primary-600 hover:text-primary-700"
        >
          View on ClinicalTrials.gov
          <ExternalLink className="w-3 h-3" />
        </a>
      </CardContent>
    </Card>
  );
}
