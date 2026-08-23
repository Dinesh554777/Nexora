import { Patient, AnalyticsSummary } from '@/types';

export const demoPatients: Patient[] = [
  { id: 'P001', age: 65, sex: 'M', meniscusThickness: 3.2, oaStatus: 'OA', analysisStatus: 'Completed' },
  { id: 'P002', age: 45, sex: 'F', meniscusThickness: 5.8, oaStatus: 'Non-OA', analysisStatus: 'Completed' },
  { id: 'P003', age: 72, sex: 'M', meniscusThickness: 2.8, oaStatus: 'OA', analysisStatus: 'Completed' },
  { id: 'P004', age: 38, sex: 'F', meniscusThickness: 6.1, oaStatus: 'Non-OA', analysisStatus: 'Completed' },
  { id: 'P005', age: 68, sex: 'F', meniscusThickness: 3.5, oaStatus: 'OA', analysisStatus: 'Completed' },
  { id: 'P006', age: 52, sex: 'M', meniscusThickness: 5.2, oaStatus: 'Non-OA', analysisStatus: 'Completed' },
  { id: 'P007', age: 70, sex: 'M', meniscusThickness: 3.0, oaStatus: 'OA', analysisStatus: 'Completed' },
  { id: 'P008', age: 42, sex: 'F', meniscusThickness: 5.5, oaStatus: 'Non-OA', analysisStatus: 'Completed' },
  { id: 'P009', age: 75, sex: 'M', meniscusThickness: 2.5, oaStatus: 'OA', analysisStatus: 'Completed' },
  { id: 'P010', age: 35, sex: 'F', meniscusThickness: 6.3, oaStatus: 'Non-OA', analysisStatus: 'Completed' },
  { id: 'P011', age: 66, sex: 'F', meniscusThickness: 3.4, oaStatus: 'OA', analysisStatus: 'Pending' },
  { id: 'P012', age: 48, sex: 'M', meniscusThickness: 5.7, oaStatus: 'Non-OA', analysisStatus: 'Completed' },
  { id: 'P013', age: 71, sex: 'M', meniscusThickness: 2.9, oaStatus: 'OA', analysisStatus: 'Completed' },
  { id: 'P014', age: 40, sex: 'F', meniscusThickness: 5.9, oaStatus: 'Non-OA', analysisStatus: 'Completed' },
  { id: 'P015', age: 69, sex: 'M', meniscusThickness: 3.3, oaStatus: 'OA', analysisStatus: 'Completed' },
];

export const demoAnalyticsSummary: AnalyticsSummary = {
  totalPatients: 15,
  oaPatients: 8,
  nonOaPatients: 7,
  oaPercentage: 53.3,
  avgMeniscusThickness: 4.3,
  minMeniscusThickness: 2.5,
  maxMeniscusThickness: 6.3,
};

// Function to calculate analytics from patient data
export const calculateAnalytics = (patients: Patient[]): AnalyticsSummary => {
  const oaPatients = patients.filter(p => p.oaStatus === 'OA').length;
  const nonOaPatients = patients.filter(p => p.oaStatus === 'Non-OA').length;
  const totalPatients = patients.length;
  const oaPercentage = totalPatients > 0 ? (oaPatients / totalPatients) * 100 : 0;
  
  const thicknesses = patients.map(p => p.meniscusThickness);
  const avgMeniscusThickness = thicknesses.reduce((a, b) => a + b, 0) / thicknesses.length;
  const minMeniscusThickness = Math.min(...thicknesses);
  const maxMeniscusThickness = Math.max(...thicknesses);

  return {
    totalPatients,
    oaPatients,
    nonOaPatients,
    oaPercentage: parseFloat(oaPercentage.toFixed(1)),
    avgMeniscusThickness: parseFloat(avgMeniscusThickness.toFixed(1)),
    minMeniscusThickness,
    maxMeniscusThickness,
  };
};
