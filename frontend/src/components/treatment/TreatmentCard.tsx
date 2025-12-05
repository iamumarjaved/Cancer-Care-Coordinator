'use client';

import { TreatmentOption } from '@/types';
import { Card, CardContent, CardHeader, CardTitle, Badge } from '@/components/ui';
import { getRecommendationColor, formatPercentage } from '@/lib/utils';
import { TrendingUp, AlertCircle, BookOpen } from 'lucide-react';

interface TreatmentCardProps {
  treatment: TreatmentOption;
}

export function TreatmentCard({ treatment }: TreatmentCardProps) {
  const recommendationLabel = treatment.recommendation
    ?.replace(/_/g, ' ')
    .replace(/\b\w/g, (l) => l.toUpperCase());

  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div>
            <div className="flex items-center gap-2">
              <Badge className="text-xs">#{treatment.rank}</Badge>
              <CardTitle className="text-base">{treatment.treatment_name}</CardTitle>
            </div>
            <p className="text-sm text-secondary-500 mt-1">{treatment.treatment_type}</p>
          </div>
          {treatment.recommendation && (
            <Badge className={getRecommendationColor(treatment.recommendation)}>
              {recommendationLabel}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Drugs */}
        {treatment.drugs && treatment.drugs.length > 0 && (
          <div>
            <p className="text-xs text-secondary-500 uppercase tracking-wide mb-1">Drugs</p>
            <div className="flex flex-wrap gap-1">
              {treatment.drugs.map((drug, index) => (
                <Badge key={index} variant="info" className="text-xs">
                  {drug}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Dosing */}
        {treatment.dosing && (
          <div>
            <p className="text-xs text-secondary-500 uppercase tracking-wide mb-1">Dosing</p>
            <p className="text-sm text-secondary-700">{treatment.dosing}</p>
          </div>
        )}

        {/* Expected Outcomes */}
        {treatment.expected_response_rate && (
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-success-500" />
            <span className="text-sm">
              Expected response rate: {formatPercentage(treatment.expected_response_rate)}
            </span>
          </div>
        )}

        {/* Confidence */}
        {treatment.confidence && (
          <div className="flex items-center gap-2">
            <div className="flex-1 h-2 bg-secondary-100 rounded-full">
              <div
                className="h-full bg-primary-500 rounded-full"
                style={{ width: `${treatment.confidence * 100}%` }}
              />
            </div>
            <span className="text-xs text-secondary-500">
              {formatPercentage(treatment.confidence)} confidence
            </span>
          </div>
        )}

        {/* Side Effects */}
        {treatment.common_side_effects && treatment.common_side_effects.length > 0 && (
          <div>
            <div className="flex items-center gap-1 mb-1">
              <AlertCircle className="w-3 h-3 text-warning-500" />
              <p className="text-xs text-secondary-500 uppercase tracking-wide">Common Side Effects</p>
            </div>
            <div className="flex flex-wrap gap-1">
              {treatment.common_side_effects.slice(0, 4).map((effect, index) => (
                <Badge key={index} variant="warning" className="text-xs">
                  {effect}
                </Badge>
              ))}
              {treatment.common_side_effects.length > 4 && (
                <Badge variant="warning" className="text-xs">
                  +{treatment.common_side_effects.length - 4} more
                </Badge>
              )}
            </div>
          </div>
        )}

        {/* Key Trials */}
        {treatment.key_trials && treatment.key_trials.length > 0 && (
          <div>
            <div className="flex items-center gap-1 mb-1">
              <BookOpen className="w-3 h-3 text-secondary-400" />
              <p className="text-xs text-secondary-500 uppercase tracking-wide">Key Trials</p>
            </div>
            <p className="text-sm text-secondary-600">{treatment.key_trials.join(', ')}</p>
          </div>
        )}

        {/* Rationale */}
        {treatment.rationale && (
          <div className="pt-2 border-t border-secondary-100">
            <p className="text-sm text-secondary-600 italic">{treatment.rationale}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
