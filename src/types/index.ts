export interface Patient {
  id: string;
  age: number;
  sex: 'M' | 'F';
  meniscusThickness: number;
  oaStatus: 'OA' | 'Non-OA';
  analysisStatus: 'Completed' | 'Pending';
  femurWidth?: number;
  femurAP?: number;
  tibiaWidth?: number;
  tibiaAP?: number;
}

export interface ImplantRecommendation {
  implantId: string;
  implantName: string;
  size: string;
  matchScore: number;
  confidence: number;
  measurementDifference: number;
  rank?: number;
}

export interface AnalyticsSummary {
  totalPatients: number;
  oaPatients: number;
  nonOaPatients: number;
  oaPercentage: number;
  avgMeniscusThickness: number;
  minMeniscusThickness: number;
  maxMeniscusThickness: number;
}

export interface PatientMeasurements {
  femurWidth: number;
  femurAP: number;
  tibiaWidth: number;
  tibiaAP: number;
}
