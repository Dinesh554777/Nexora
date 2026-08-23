import { Patient } from '@/types';

export interface DescriptiveStats {
  count: number;
  mean: number;
  min: number;
  max: number;
}

export function calculateMean(values: number[]): number {
  if (values.length === 0) return 0;
  return values.reduce((sum, val) => sum + val, 0) / values.length;
}

export function calculatePercentage(part: number, total: number): number {
  if (total === 0) return 0;
  return (part / total) * 100;
}

export function getDescriptiveStats(values: number[]): DescriptiveStats {
  if (values.length === 0) {
    return { count: 0, mean: 0, min: 0, max: 0 };
  }

  return {
    count: values.length,
    mean: calculateMean(values),
    min: Math.min(...values),
    max: Math.max(...values),
  };
}

export function filterPatientsByAge(patients: Patient[], minAge: number, maxAge: number): Patient[] {
  return patients.filter(p => p.age >= minAge && p.age <= maxAge);
}

export function filterPatientsBySex(patients: Patient[], sex: 'M' | 'F'): Patient[] {
  return patients.filter(p => p.sex === sex);
}

export function filterPatientsByOAStatus(patients: Patient[], status: 'OA' | 'Non-OA' | 'All'): Patient[] {
  if (status === 'All') return patients;
  return patients.filter(p => p.oaStatus === status);
}
