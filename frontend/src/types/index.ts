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

// Medical Imaging Types
export interface UploadedImage {
  id: string;
  file: File;
  preview: string;
  type: 'xray' | 'mri';
  uploadedAt: Date;
}

export interface ImageAnalysisResult {
  imageId: string;
  findings: string[];
  confidence: number;
  abnormalRegions: Array<{
    region: string;
    description: string;
    severity: 'low' | 'medium' | 'high';
  }>;
  measurements?: {
    meniscusThickness?: number;
    jointSpaceWidth?: number;
  };
  oaIndicators?: {
    present: boolean;
    severity: 'none' | 'mild' | 'moderate' | 'severe';
    observations: string[];
  };
  timestamp: Date;
}

export type AnalysisState = 'ready' | 'uploading' | 'processing' | 'complete' | 'failed';

// Export Types
export interface ExportData {
  patientInfo?: {
    patientId?: string;
    age?: string;
    sex?: string;
  };
  measurements?: PatientMeasurements;
  recommendation?: ImplantRecommendation;
  alternatives?: ImplantRecommendation[];
  imageAnalysis?: ImageAnalysisResult[];
  timestamp: Date;
}
