import { useState } from 'react';
import { PageHeader } from '@/components/shared/PageHeader';
import { PatientInfoForm, PatientInfo } from '@/components/implant/PatientInfoForm';
import { ComparisonTimeline } from '@/components/progress/ComparisonTimeline';
import { MetricComparisonTable } from '@/components/progress/MetricComparisonTable';
import { SideBySideVisuals } from '@/components/progress/SideBySideVisuals';
import { PrintComparisonModal } from '@/components/progress/PrintComparisonModal';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  Upload,
  Calendar,
  History,
  FileText,
  Loader2,
  AlertTriangle,
  RotateCcw,
  Sparkles,
} from 'lucide-react';
import { UploadedImage, ImageAnalysisResult, AnalysisState } from '@/types';
import { apiService } from '@/services/api';

export function ProgressView() {
  const [patientInfo, setPatientInfo] = useState<PatientInfo>({
    patientName: '',
    patientId: '',
    age: '',
    sex: '',
  });

  const [previousDate, setPreviousDate] = useState<string>('2025-08-15');
  const [currentDate, setCurrentDate] = useState<string>('2026-08-23');

  const [previousImage, setPreviousImage] = useState<UploadedImage | null>(null);
  const [currentImage, setCurrentImage] = useState<UploadedImage | null>(null);

  const [previousResult, setPreviousResult] = useState<ImageAnalysisResult | null>(null);
  const [currentResult, setCurrentResult] = useState<ImageAnalysisResult | null>(null);

  const [analysisState, setAnalysisState] = useState<AnalysisState>('ready');
  const [error, setError] = useState<string | null>(null);
  const [isPrintModalOpen, setIsPrintModalOpen] = useState(false);

  // Date validation: Current date should not be earlier than previous date
  const isDateInvalid = (() => {
    if (!previousDate || !currentDate) return false;
    const prev = new Date(previousDate).getTime();
    const curr = new Date(currentDate).getTime();
    return !isNaN(prev) && !isNaN(curr) && curr < prev;
  })();

  const handleFileUpload = (
    e: React.ChangeEvent<HTMLInputElement>,
    type: 'previous' | 'current'
  ) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    const validTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/tiff', 'image/bmp'];
    if (!validTypes.includes(file.type)) {
      setError('Please select a valid image file (JPEG, PNG, WebP, TIFF, or BMP).');
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      const uploaded: UploadedImage = {
        id: `${type}-${Date.now()}`,
        file,
        preview: reader.result as string,
        type: 'xray',
        uploadedAt: new Date(),
      };

      if (type === 'previous') {
        setPreviousImage(uploaded);
        setPreviousResult(null);
      } else {
        setCurrentImage(uploaded);
        setCurrentResult(null);
      }
      setError(null);
    };
    reader.readAsDataURL(file);
  };

  const handleRunComparison = async () => {
    if (!previousImage || !currentImage) {
      setError('Please upload both the Previous Scan and Current Scan to generate a comparison.');
      return;
    }

    if (isDateInvalid) {
      setError('Current scan date cannot be earlier than previous scan date. Please correct the dates.');
      return;
    }

    setAnalysisState('processing');
    setError(null);

    try {
      // 1. Run real backend analysis for Previous Scan
      const prevFormData = new FormData();
      prevFormData.append('file', previousImage.file);
      const prevResponse = await apiService.segmentImage(prevFormData);

      const prevMetrics = prevResponse.metrics ?? {};
      const normalizeBase64 = (val?: string) => {
        if (!val) return undefined;
        return val.startsWith('data:image') ? val : `data:image/png;base64,${val}`;
      };

      const realPrevResult: ImageAnalysisResult = {
        imageId: previousImage.id,
        filename: prevResponse.filename,
        findings: [
          'The previous baseline knee scan was processed successfully by the Nexora AI segmentation pipeline.',
        ],
        confidence: typeof prevMetrics.probability_mean === 'number'
          ? Math.max(0, Math.min(100, Math.round(prevMetrics.probability_mean * 100)))
          : 95,
        abnormalRegions: [],
        originalImageBase64: previousImage.preview,
        maskImageBase64: normalizeBase64(prevResponse.mask_image_base64),
        overlayImageBase64: normalizeBase64(prevResponse.overlay_image_base64),
        technicalMetrics: {
          probabilityMean: typeof prevMetrics.probability_mean === 'number' ? Number(prevMetrics.probability_mean) : undefined,
          maskAreaPixels: typeof prevMetrics.mask_area_pixels === 'number' ? Number(prevMetrics.mask_area_pixels) : undefined,
          maskFraction: typeof prevMetrics.mask_fraction === 'number' ? Number(prevMetrics.mask_fraction) : undefined,
          threshold: typeof prevMetrics.threshold === 'number' ? Number(prevMetrics.threshold) : 0.5,
        },
        timestamp: new Date(previousDate || Date.now()),
      };

      // 2. Run real backend analysis for Current Scan
      const currFormData = new FormData();
      currFormData.append('file', currentImage.file);
      const currResponse = await apiService.segmentImage(currFormData);

      const currMetrics = currResponse.metrics ?? {};
      const realCurrResult: ImageAnalysisResult = {
        imageId: currentImage.id,
        filename: currResponse.filename,
        findings: [
          'The current follow-up knee scan was processed successfully by the Nexora AI segmentation pipeline.',
        ],
        confidence: typeof currMetrics.probability_mean === 'number'
          ? Math.max(0, Math.min(100, Math.round(currMetrics.probability_mean * 100)))
          : 95,
        abnormalRegions: [],
        originalImageBase64: currentImage.preview,
        maskImageBase64: normalizeBase64(currResponse.mask_image_base64),
        overlayImageBase64: normalizeBase64(currResponse.overlay_image_base64),
        technicalMetrics: {
          probabilityMean: typeof currMetrics.probability_mean === 'number' ? Number(currMetrics.probability_mean) : undefined,
          maskAreaPixels: typeof currMetrics.mask_area_pixels === 'number' ? Number(currMetrics.mask_area_pixels) : undefined,
          maskFraction: typeof currMetrics.mask_fraction === 'number' ? Number(currMetrics.mask_fraction) : undefined,
          threshold: typeof currMetrics.threshold === 'number' ? Number(currMetrics.threshold) : 0.5,
        },
        timestamp: new Date(currentDate || Date.now()),
      };

      setPreviousResult(realPrevResult);
      setCurrentResult(realCurrResult);
      setAnalysisState('complete');
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Analysis failed during scan processing.';
      setError(`Comparison Analysis Failed: ${msg}`);
      setAnalysisState('failed');
      setPreviousResult(null);
      setCurrentResult(null);
    }
  };

  const handleClear = () => {
    setPreviousImage(null);
    setCurrentImage(null);
    setPreviousResult(null);
    setCurrentResult(null);
    setAnalysisState('ready');
    setError(null);
  };

  const isComparisonReady = Boolean(
    analysisState === 'complete' && previousResult && currentResult
  );

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <PageHeader
        title="Nexora Progress View"
        description="Previous vs Current AI Scan Comparison for longitudinal image analysis"
      />

      {/* Patient Demographic Form */}
      <PatientInfoForm
        patientInfo={patientInfo}
        onChange={setPatientInfo}
      />

      {/* Scan Setup Card (Previous vs Current Uploads & Dates) */}
      <Card className="border-primary/20 shadow-sm">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <History className="h-5 w-5 text-primary" />
            Scan Selection & Acquisition Dates
          </CardTitle>
          <CardDescription>
            Specify the acquisition dates and upload the corresponding knee X-ray images for longitudinal comparison.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Dual Upload Slots */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Slot A: Previous Scan */}
            <div className="rounded-xl border-2 border-dashed border-slate-300 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-900/20 p-5 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase text-slate-700 dark:text-slate-300 tracking-wider flex items-center gap-1.5">
                  <Calendar className="h-4 w-4 text-slate-500" />
                  Previous Scan (Baseline)
                </span>
                {previousImage && (
                  <span className="text-xs font-semibold text-green-600 bg-green-50 dark:bg-green-950 px-2 py-0.5 rounded border border-green-200">
                    Image Loaded
                  </span>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="prevDate" className="text-xs">Acquisition Date</Label>
                <Input
                  id="prevDate"
                  type="date"
                  value={previousDate}
                  onChange={(e) => setPreviousDate(e.target.value)}
                  className="bg-background"
                />
              </div>

              {previousImage ? (
                <div className="space-y-3">
                  <div className="h-44 bg-black rounded-lg overflow-hidden flex items-center justify-center p-1 border">
                    <img
                      src={previousImage.preview}
                      alt="Previous Scan Preview"
                      className="max-h-40 max-w-full object-contain"
                    />
                  </div>
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span className="truncate max-w-[200px]">{previousImage.file.name}</span>
                    <label
                      htmlFor="prev-file-input"
                      className="text-primary hover:underline cursor-pointer font-medium"
                    >
                      Change image
                    </label>
                  </div>
                </div>
              ) : (
                <label
                  htmlFor="prev-file-input"
                  className="flex flex-col items-center justify-center h-44 rounded-lg border border-dashed hover:border-primary/50 hover:bg-muted/40 cursor-pointer transition-colors p-4 text-center"
                >
                  <Upload className="h-8 w-8 text-muted-foreground mb-2" />
                  <span className="text-sm font-semibold text-foreground">Upload Previous Knee X-Ray</span>
                  <span className="text-xs text-muted-foreground mt-1">PNG, JPG, WebP, TIFF up to 25MB</span>
                </label>
              )}
              <input
                id="prev-file-input"
                type="file"
                accept="image/*"
                className="hidden"
                onChange={(e) => handleFileUpload(e, 'previous')}
              />
            </div>

            {/* Slot B: Current Scan */}
            <div className="rounded-xl border-2 border-dashed border-primary/30 bg-primary/5 p-5 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase text-primary tracking-wider flex items-center gap-1.5">
                  <Calendar className="h-4 w-4 text-primary" />
                  Current Scan (Follow-up)
                </span>
                {currentImage && (
                  <span className="text-xs font-semibold text-green-600 bg-green-50 dark:bg-green-950 px-2 py-0.5 rounded border border-green-200">
                    Image Loaded
                  </span>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="currDate" className="text-xs">Acquisition Date</Label>
                <Input
                  id="currDate"
                  type="date"
                  value={currentDate}
                  onChange={(e) => setCurrentDate(e.target.value)}
                  className="bg-background"
                />
              </div>

              {currentImage ? (
                <div className="space-y-3">
                  <div className="h-44 bg-black rounded-lg overflow-hidden flex items-center justify-center p-1 border">
                    <img
                      src={currentImage.preview}
                      alt="Current Scan Preview"
                      className="max-h-40 max-w-full object-contain"
                    />
                  </div>
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span className="truncate max-w-[200px]">{currentImage.file.name}</span>
                    <label
                      htmlFor="curr-file-input"
                      className="text-primary hover:underline cursor-pointer font-medium"
                    >
                      Change image
                    </label>
                  </div>
                </div>
              ) : (
                <label
                  htmlFor="curr-file-input"
                  className="flex flex-col items-center justify-center h-44 rounded-lg border border-dashed border-primary/40 hover:border-primary hover:bg-primary/10 cursor-pointer transition-colors p-4 text-center"
                >
                  <Upload className="h-8 w-8 text-primary mb-2" />
                  <span className="text-sm font-semibold text-foreground">Upload Current Knee X-Ray</span>
                  <span className="text-xs text-muted-foreground mt-1">PNG, JPG, WebP, TIFF up to 25MB</span>
                </label>
              )}
              <input
                id="curr-file-input"
                type="file"
                accept="image/*"
                className="hidden"
                onChange={(e) => handleFileUpload(e, 'current')}
              />
            </div>
          </div>

          {/* Validation Warning */}
          {isDateInvalid && (
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Invalid Date Sequence</AlertTitle>
              <AlertDescription>
                The Current Scan Date ({currentDate}) cannot be earlier than the Previous Scan Date ({previousDate}). Please adjust the dates before proceeding.
              </AlertDescription>
            </Alert>
          )}

          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-3 pt-2">
            <Button
              onClick={handleRunComparison}
              disabled={
                !previousImage ||
                !currentImage ||
                isDateInvalid ||
                analysisState === 'processing'
              }
              className="flex-1 gap-2 font-semibold shadow-sm"
            >
              {analysisState === 'processing' ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Analyzing Both Scans with U-Net...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  Analyze Scans & Generate Comparison
                </>
              )}
            </Button>
            <Button
              variant="outline"
              onClick={handleClear}
              disabled={analysisState === 'processing'}
              className="gap-1.5"
            >
              <RotateCcw className="h-4 w-4" />
              Clear
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Comparison Results Section */}
      {isComparisonReady && previousResult && currentResult && (
        <div className="space-y-6 animate-in fade-in-50 duration-300">
          {/* Comparison Header Banner */}
          <div className="rounded-xl border bg-card p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-sm">
            <div>
              <p className="text-xs uppercase font-bold text-primary tracking-wider">Nexora Progress View</p>
              <h2 className="text-lg font-bold text-foreground">
                Previous vs Current AI Scan Comparison
              </h2>
              <p className="text-xs text-muted-foreground mt-0.5">
                Patient: <span className="font-semibold text-foreground">{patientInfo.patientName || patientInfo.patientId || 'Not specified'}</span>
                {patientInfo.patientId && patientInfo.patientName && ` (ID: ${patientInfo.patientId})`}
              </p>
            </div>
            <Button
              onClick={() => setIsPrintModalOpen(true)}
              className="gap-2 font-semibold shadow-sm"
            >
              <FileText className="h-4 w-4" />
              Print Comparison Report
            </Button>
          </div>

          {/* Timeline */}
          <ComparisonTimeline
            previousDate={previousDate}
            currentDate={currentDate}
          />

          {/* Side-by-Side Visuals */}
          <SideBySideVisuals
            previousResult={previousResult}
            currentResult={currentResult}
            previousImage={previousImage || undefined}
            currentImage={currentImage || undefined}
            previousDate={previousDate}
            currentDate={currentDate}
          />

          {/* Real AI Metric Comparison Table */}
          <MetricComparisonTable
            previousResult={previousResult}
            currentResult={currentResult}
          />

          {/* Technical Comparison Summary */}
          <div className="rounded-xl border bg-muted/20 p-4 space-y-1.5">
            <h4 className="text-xs font-bold uppercase text-primary tracking-wider">
              Technical Comparison Summary
            </h4>
            <p className="text-xs text-muted-foreground leading-relaxed">
              The comparison shows differences between the previous and current AI-generated segmentation outputs. Changes in technical metrics are displayed above for clinical review.
            </p>
          </div>

          {/* Safety Disclaimer */}
          <Alert className="border-amber-200 bg-amber-50 dark:bg-amber-950/40 dark:border-amber-900">
            <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400" />
            <AlertDescription className="text-xs text-amber-800 dark:text-amber-300 leading-relaxed">
              <strong>Clinical Safety Disclaimer:</strong> This comparison presents differences between AI-generated image analysis outputs from two scans. It is intended to support clinical review and does not independently diagnose disease progression, improvement, or any medical condition. Final interpretation must be made by a qualified healthcare professional.
            </AlertDescription>
          </Alert>

          {/* Print Modal */}
          <PrintComparisonModal
            isOpen={isPrintModalOpen}
            onClose={() => setIsPrintModalOpen(false)}
            previousResult={previousResult}
            currentResult={currentResult}
            previousImage={previousImage || undefined}
            currentImage={currentImage || undefined}
            previousDate={previousDate}
            currentDate={currentDate}
            patientInfo={patientInfo}
          />
        </div>
      )}
    </div>
  );
}

