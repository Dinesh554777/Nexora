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

export interface OAAssessment {
  classification: 'OA' | 'NON_OA';
  confidence: number;           // 0–1
  severity: 'None' | 'Mild' | 'Moderate' | 'Severe';
  findings: {
    reduced_meniscal_signal: boolean;
    meniscal_coverage_loss: boolean;
    structural_irregularity: boolean;
  };
  notes: string;
  source: string;
  clinical_warning: string;
}

export interface ImageAnalysisResult {
  imageId: string;
  filename?: string;
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
  oaAssessment?: OAAssessment;
  originalImageBase64?: string;
  maskImageBase64?: string;
  overlayImageBase64?: string;
  technicalMetrics?: {
    probabilityMean?: number;
    maskAreaPixels?: number;
    maskFraction?: number;
    threshold?: number;
  };
  timestamp: Date;
}

export type AnalysisState = 'ready' | 'uploading' | 'processing' | 'complete' | 'failed';

// Patient Medical Result Report Types
export interface PatientMedicalReportData {
  reportId: string;
  generatedAt: Date;
  patientInfo: {
    patientName?: string;
    patientId?: string;
    age?: string;
    sex?: string;
  };
  analysisResult: ImageAnalysisResult;
  imageType?: 'xray' | 'mri';
  status: 'Completed' | 'Pending' | 'Failed';
}

// Progress Comparison Types
export interface MetricDifference {
  metricName: string;
  previousValue: number | undefined;
  currentValue: number | undefined;
  previousFormatted: string;
  currentFormatted: string;
  differenceFormatted: string;
  differenceType: 'positive' | 'negative' | 'neutral' | 'unavailable';
}

export interface ScanComparisonData {
  patientInfo?: {
    patientName?: string;
    patientId?: string;
    age?: string;
    sex?: string;
  };
  previousScan: {
    date: string;
    image: UploadedImage;
    result: ImageAnalysisResult;
  };
  currentScan: {
    date: string;
    image: UploadedImage;
    result: ImageAnalysisResult;
  };
  metricDifferences: MetricDifference[];
  summary: string;
}

// Export Types
export interface ExportData {
  patientInfo?: {
    patientId?: string;
    patientName?: string;
    age?: string;
    sex?: string;
  };
  measurements?: PatientMeasurements;
  recommendation?: ImplantRecommendation;
  alternatives?: ImplantRecommendation[];
  imageAnalysis?: ImageAnalysisResult[];
  timestamp: Date;
}
