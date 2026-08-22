// API Request Types
export interface PatientMeasurementsRequest {
  femurWidth: number;
  femurAP: number;
  tibiaWidth: number;
  tibiaAP: number;
}

// API Response Types
export interface ImplantRecommendationAPI {
  implantId: string;
  implantName: string;
  size: string;
  matchScore: number;
  confidence: number;
  measurementDifference: number;
  rank?: number;
}

export interface ImplantMatchResponse {
  recommendation: ImplantRecommendationAPI;
  alternatives: ImplantRecommendationAPI[];
}

export interface PatientRecordAPI {
  id: string;
  age: number;
  sex: 'M' | 'F';
  meniscusThickness: number;
  oaStatus: 'OA' | 'Non-OA';
  analysisStatus: 'Completed' | 'Pending';
}

export interface AgeDistribution {
  age: string;
  OA: number;
  NonOA: number;
}

export interface SexDistribution {
  sex: string;
  OA: number;
  NonOA: number;
}

export interface AnalyticsResponse {
  totalPatients: number;
  oaPatients: number;
  nonOaPatients: number;
  oaPercentage: number;
  avgMeniscusThickness: number;
  minMeniscusThickness: number;
  maxMeniscusThickness: number;
  patients: PatientRecordAPI[];
  ageDistribution: AgeDistribution[];
  sexDistribution: SexDistribution[];
}

// Error Response
export interface APIError {
  detail: string;
}
