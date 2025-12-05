'use client';

import Link from 'next/link';
import { Card, CardContent, Button } from '@/components/ui';
import { Play, FlaskConical, Dna, BookOpen, Pill } from 'lucide-react';

interface RunAnalysisPromptProps {
  patientId: string;
  tabName: string;
  description: string;
  icon?: 'trials' | 'genomics' | 'evidence' | 'treatment';
}

const iconMap = {
  trials: FlaskConical,
  genomics: Dna,
  evidence: BookOpen,
  treatment: Pill,
};

export function RunAnalysisPrompt({ patientId, tabName, description, icon = 'trials' }: RunAnalysisPromptProps) {
  const Icon = iconMap[icon];

  return (
    <Card className="border-dashed border-2 border-gray-300">
      <CardContent className="py-16 text-center">
        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
          <Icon className="w-8 h-8 text-gray-400" />
        </div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          No {tabName} Data Available
        </h3>
        <p className="text-gray-500 mb-6 max-w-md mx-auto">
          {description}
        </p>
        <Link href={`/patients/${patientId}/analysis`}>
          <Button size="lg">
            <Play className="w-5 h-5 mr-2" />
            Run Analysis to Get {tabName}
          </Button>
        </Link>
        <p className="text-xs text-gray-400 mt-4">
          The AI will analyze the patient data and generate personalized {tabName.toLowerCase()}.
        </p>
      </CardContent>
    </Card>
  );
}
