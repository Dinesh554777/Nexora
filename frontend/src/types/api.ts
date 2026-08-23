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

export interface SegmentMetricsResponse {
  mask_area_pixels?: number;
  mask_fraction?: number;
  probability_mean?: number;
  threshold?: number;
  [key: string]: unknown;
}

export interface OAAssessmentRaw {
  classification: string;
  confidence: number;
  severity: string;
  findings: {
    reduced_meniscal_signal: boolean;
    meniscal_coverage_loss: boolean;
    structural_irregularity: boolean;
  };
  notes: string;
  source: string;
  clinical_warning: string;
}

export interface SegmentImageResponse {
  success: boolean;
  filename: string;
  mask_image_base64: string;
  overlay_image_base64: string;
  oa_assessment?: OAAssessmentRaw;
  metrics: SegmentMetricsResponse;
  metadata: Record<string, unknown>;
}

// Error Response
export interface APIError {
  detail: string;
}

// ── Demo Cases ──────────────────────────────────────────────────────────────

export interface DemoCaseCard {
  case_id: string;
  case_type: 'OA' | 'NON_OA';
  label: string;
  patient_id: string;
  age: number;
  sex: string;
  affected_knee: string;
  classification: string;
  severity: string;
  confidence: number;
  scan_type: string;
  scan_date: string;
  report_status: string;
  demo: boolean;
  clinical_use: boolean;
  disclaimer: string;
}

export interface DemoCasesListResponse {
  demo: boolean;
  clinical_use: boolean;
  disclaimer: string;
  total: number;
  cases: DemoCaseCard[];
}

export interface DemoReportAssessment {
  case_id: string;
  classification: string;
  oa_status: string;
  confidence: number;
  severity: string;
  source: string;
  model_version: string | null;
  is_demo: boolean;
  clinical_warning: string;
}

export interface DemoReportSegmentation {
  mask_area_pixels: number | null;
  mask_fraction: number | null;
  probability_mean: number | null;
  threshold: number;
  model_name: string;
  source: string;
}

export interface DemoReportMeasurements {
  medial_meniscus_thickness_mm?: number;
  lateral_meniscus_thickness_mm?: number;
  medial_joint_space_mm?: number;
  lateral_joint_space_mm?: number;
  femur_width_mm?: number;
  femur_ap_mm?: number;
  tibia_width_mm?: number;
  tibia_ap_mm?: number;
}

export interface DemoReportImplantRecommendation {
  implantId: string;
  implantName: string;
  size: string;
  matchScore: number;
  confidence: number;
  measurementDifference: number;
  rank: number;
}

export interface DemoReportImplantAssessment {
  required: boolean;
  status: string;
  recommendation: DemoReportImplantRecommendation | null;
  alternatives: DemoReportImplantRecommendation[];
  note: string;
}

export interface DemoReport {
  report_id: string;
  report_version: string;
  generated_at: string;
  demo: boolean;
  clinical_use: boolean;
  report_status: string;
  disclaimer: string;
  patient: {
    patient_id: string;
    name: string;
    age: number;
    sex: string;
    affected_knee: string;
  };
  scan: {
    scan_type: string;
    scan_date: string;
  };
  assessment: DemoReportAssessment;
  segmentation: DemoReportSegmentation;
  measurements: DemoReportMeasurements;
  findings: string[];
  implant_assessment: DemoReportImplantAssessment;
  pipeline_stages: string[];
}

// ── OA Assessment ────────────────────────────────────────────────────────────

export interface OAAssessmentResponse {
  case_id: string;
  assessment: {
    classification: string;
    oa_status: string;
    confidence: number;
    severity: string;
  };
  source: string;
  model_version: string | null;
  is_demo: boolean;
  status: string;
  clinical_warning: string;
  image_info: {
    filename: string;
    width: number;
    height: number;
  };
  metadata: Record<string, unknown>;
}
