import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { format, formatDistanceToNow, parseISO } from 'date-fns';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? parseISO(date) : date;
  return format(d, 'MMM d, yyyy');
}

export function formatDateTime(date: string | Date | undefined | null): string {
  if (!date) return 'N/A';
  try {
    const d = typeof date === 'string' ? parseISO(date) : date;
    if (isNaN(d.getTime())) return 'N/A';
    return format(d, 'MMM d, yyyy HH:mm');
  } catch {
    return 'N/A';
  }
}

export function formatRelativeTime(date: string | Date): string {
  const d = typeof date === 'string' ? parseISO(date) : date;
  return formatDistanceToNow(d, { addSuffix: true });
}

export function calculateAge(dateOfBirth: string): number {
  const today = new Date();
  const birthDate = parseISO(dateOfBirth);
  let age = today.getFullYear() - birthDate.getFullYear();
  const monthDiff = today.getMonth() - birthDate.getMonth();
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
    age--;
  }
  return age;
}

export function formatPercentage(value: number, decimals: number = 0): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

export function formatCancerStage(stage: string): string {
  return stage.replace('_', ' ').replace('Stage ', 'Stage ');
}

export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    completed: 'text-green-600 bg-green-50',
    in_progress: 'text-blue-600 bg-blue-50',
    pending: 'text-yellow-600 bg-yellow-50',
    error: 'text-red-600 bg-red-50',
    recruiting: 'text-green-600 bg-green-50',
    active: 'text-blue-600 bg-blue-50',
    terminated: 'text-red-600 bg-red-50',
  };
  return colors[status.toLowerCase()] || 'text-gray-600 bg-gray-50';
}

export function getRecommendationColor(level: string): string {
  const colors: Record<string, string> = {
    strongly_recommended: 'text-green-700 bg-green-100 border-green-200',
    recommended: 'text-blue-700 bg-blue-100 border-blue-200',
    consider: 'text-yellow-700 bg-yellow-100 border-yellow-200',
    not_recommended: 'text-orange-700 bg-orange-100 border-orange-200',
    contraindicated: 'text-red-700 bg-red-100 border-red-200',
  };
  return colors[level] || 'text-gray-700 bg-gray-100 border-gray-200';
}

export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + '...';
}

export function formatGeneMutation(gene: string, variant: string): string {
  return `${gene} ${variant}`;
}

export function parseTrialPhase(phase: string): number {
  const phaseMap: Record<string, number> = {
    'Phase I': 1,
    'Phase I/II': 1.5,
    'Phase II': 2,
    'Phase II/III': 2.5,
    'Phase III': 3,
    'Phase IV': 4,
  };
  return phaseMap[phase] || 0;
}
