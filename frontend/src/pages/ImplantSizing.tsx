import { useState } from 'react';
import { PageHeader } from '@/components/shared/PageHeader';
import { MeasurementForm } from '@/components/implant/MeasurementForm';
import { ImplantRecommendation } from '@/components/implant/ImplantRecommendation';
import { AlternativeMatches } from '@/components/implant/AlternativeMatches';
import { PatientInfoForm, PatientInfo } from '@/components/implant/PatientInfoForm';
import { StepIndicator } from '@/components/shared/StepIndicator';
import { AnalysisSuccess } from '@/components/implant/AnalysisSuccess';
import { MatchScoreDisplay } from '@/components/implant/MatchScoreDisplay';
import { ClinicalDisclaimer } from '@/components/shared/ClinicalDisclaimer';
import { ErrorRetry } from '@/components/shared/ErrorRetry';
import { ExportButton } from '@/components/implant/ExportButton';
import { AnalysisSummary } from '@/components/implant/AnalysisSummary';
import { MeasurementSummary } from '@/components/implant/MeasurementSummary';
import { WhyThisImplant } from '@/components/implant/WhyThisImplant';
import { ImplantComparison } from '@/components/implant/ImplantComparison';
import { ClinicalReview } from '@/components/implant/ClinicalReview';
import { AnalysisTimeline } from '@/components/implant/AnalysisTimeline';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Loader2 } from 'lucide-react';
import { PatientMeasurements, ImplantRecommendation as ImplantRec, ExportData } from '@/types';
import { apiService } from '@/services/api';

const steps = [
  { label: 'Patient Data', description: 'Demographics' },
  { label: 'Measurements', description: 'Knee dimensions' },
  { label: 'AI Analysis', description: 'Processing' },
  { label: 'Recommendation', description: 'Results' },
];

export function ImplantSizing() {
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [recommendation, setRecommendation] = useState<ImplantRec | null>(null);
  const [alternatives, setAlternatives] = useState<ImplantRec[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [measurements, setMeasurements] = useState<PatientMeasurements | null>(null);
  const [patientInfo, setPatientInfo] = useState<PatientInfo>({
    patientId: '',
    age: '',
    sex: '',
  });

  const handleAnalyze = async (inputMeasurements: PatientMeasurements) => {
    setLoading(true);
    setError(null);
    setMeasurements(inputMeasurements); // Store measurements
    setCurrentStep(3); // Move to Analysis step

    try {
      const response = await apiService.matchImplant(inputMeasurements);
      
      // Convert API response to frontend types
      const apiRecommendation: ImplantRec = {
        implantId: response.recommendation.implantId,
        implantName: response.recommendation.implantName,
        size: response.recommendation.size,
        matchScore: response.recommendation.matchScore,
        confidence: response.recommendation.confidence,
        measurementDifference: response.recommendation.measurementDifference,
        rank: response.recommendation.rank,
      };

      const apiAlternatives: ImplantRec[] = response.alternatives.map(alt => ({
        implantId: alt.implantId,
        implantName: alt.implantName,
        size: alt.size,
        matchScore: alt.matchScore,
        confidence: alt.confidence,
        measurementDifference: alt.measurementDifference,
        rank: alt.rank,
      }));

      setRecommendation(apiRecommendation);
      setAlternatives(apiAlternatives);
      setCurrentStep(4); // Move to Results step
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An unexpected error occurred';
      setError(errorMessage);
      setCurrentStep(2); // Return to Measurements step on error
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setRecommendation(null);
    setAlternatives([]);
    setMeasurements(null);
    setError(null);
    setCurrentStep(1);
  };

  const handleRetry = () => {
    setError(null);
    setCurrentStep(2);
  };

  // Prepare export data
  const exportData: ExportData = {
    patientInfo: patientInfo.patientId || patientInfo.age || patientInfo.sex ? {
      patientId: patientInfo.patientId,
      age: patientInfo.age,
      sex: patientInfo.sex,
    } : undefined,
    measurements: measurements || undefined,
    recommendation: recommendation || undefined,
    alternatives,
    timestamp: new Date(),
  };

  return (
    <div className="space-y-8">
      <div className="flex items-start justify-between">
        <PageHeader
          title="Implant Sizing & Matching"
          description="AI-powered knee implant recommendation based on patient measurements"
        />
        {currentStep === 4 && recommendation && (
          <ExportButton exportData={exportData} />
        )}
      </div>

      <StepIndicator steps={steps} currentStep={currentStep} />

      {error && (
        <ErrorRetry
          title="Analysis Failed"
          message={error}
          onRetry={handleRetry}
        />
      )}

      {loading && (
        <Card>
          <CardContent className="p-12">
            <div className="flex flex-col items-center justify-center space-y-4">
              <Loader2 className="h-12 w-12 animate-spin text-primary" />
              <div className="text-center">
                <p className="text-lg font-semibold">Analyzing knee measurements...</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Our AI is processing your data to find the optimal implant match
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {!loading && currentStep === 4 && recommendation && (
        <AnalysisSuccess />
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-6">
          {currentStep >= 1 && (
            <PatientInfoForm
              patientInfo={patientInfo}
              onChange={(info) => {
                setPatientInfo(info);
                if (currentStep === 1 && (info.patientId || info.age || info.sex)) {
                  setCurrentStep(2);
                }
              }}
            />
          )}
          
          {currentStep >= 2 && !loading && (
            <MeasurementForm
              onAnalyze={handleAnalyze}
              onClear={handleClear}
              loading={loading}
            />
          )}
        </div>

        <div className="space-y-6">
          {currentStep === 4 && recommendation && measurements && (
            <>
              <AnalysisSummary recommendation={recommendation} />
              <MeasurementSummary measurements={measurements} />
              <MatchScoreDisplay score={recommendation.matchScore} />
              <ImplantRecommendation recommendation={recommendation} />
              <WhyThisImplant recommendation={recommendation} />
              <AnalysisTimeline />
              {alternatives.length > 0 && (
                <>
                  <Separator className="my-6" />
                  <ImplantComparison recommendation={recommendation} alternatives={alternatives} />
                  <AlternativeMatches alternatives={alternatives} />
                </>
              )}
              <ClinicalReview />
            </>
          )}

          {currentStep < 4 && !loading && (
            <Card className="border-dashed">
              <CardHeader>
                <CardTitle>Implant Recommendation</CardTitle>
                <CardDescription>Results will appear here after analysis</CardDescription>
              </CardHeader>
              <CardContent className="flex items-center justify-center py-12">
                <p className="text-muted-foreground">
                  Complete the measurements and run analysis to view recommendations
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      <ClinicalDisclaimer />
    </div>
  );
}
