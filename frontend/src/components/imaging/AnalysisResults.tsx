import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { Progress } from '@/components/ui/progress';
import {
  AlertTriangle,
  CheckCircle2,
  Eye,
  FileText,
  Printer,
  Sparkles,
  Layers,
} from 'lucide-react';
import { ImageAnalysisResult, UploadedImage } from '@/types';
import { PatientInfo } from '@/components/implant/PatientInfoForm';
import { PatientMedicalReportModal } from './PatientMedicalReportModal';

interface AnalysisResultsProps {
  results: ImageAnalysisResult[];
  uploadedImages?: UploadedImage[];
  patientInfo?: PatientInfo;
}

export function AnalysisResults({ results, uploadedImages = [], patientInfo }: AnalysisResultsProps) {
  const [selectedResultForReport, setSelectedResultForReport] = useState<ImageAnalysisResult | null>(null);
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);

  if (results.length === 0) {
    return null;
  }

  const handleOpenReport = (result?: ImageAnalysisResult) => {
    setSelectedResultForReport(result || results[0]);
    setIsReportModalOpen(true);
  };

  return (
    <div className="space-y-6">
      {/* Top Clinical Alert */}
      <Alert className="border-orange-200 bg-orange-50 dark:bg-orange-950 dark:border-orange-900">
        <AlertTriangle className="h-5 w-5 text-orange-600 dark:text-orange-400" />
        <AlertTitle className="text-orange-800 dark:text-orange-200">
          AI-Assisted Analysis Notice
        </AlertTitle>
        <AlertDescription className="text-orange-700 dark:text-orange-300">
          AI-assisted analysis is intended to support clinical decision-making and does not replace professional medical diagnosis. All findings require review and confirmation by a qualified healthcare professional.
        </AlertDescription>
      </Alert>

      {/* Results Actions Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-xl border bg-card">
        <div>
          <p className="text-xs uppercase font-semibold text-primary tracking-wider">Analysis Complete</p>
          <p className="text-lg font-bold text-foreground">
            {results.length} Medical Image{results.length !== 1 ? 's' : ''} Processed Successfully
          </p>
          {patientInfo?.patientName && (
            <p className="text-xs text-muted-foreground mt-0.5">
              Patient: <span className="font-semibold text-foreground">{patientInfo.patientName}</span>
              {patientInfo.patientId && ` (ID: ${patientInfo.patientId})`}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button
            onClick={() => handleOpenReport(results[0])}
            className="gap-2 shadow-sm font-semibold"
          >
            <FileText className="h-4 w-4" />
            Generate Medical Report
          </Button>
        </div>
      </div>

      {/* Result Cards for Each Analyzed Image */}
      {results.map((result, index) => {
        const correspondingUpload = uploadedImages.find(img => img.id === result.imageId);
        const originalSrc = result.originalImageBase64 || correspondingUpload?.preview;
        const maskSrc = result.maskImageBase64;
        const overlaySrc = result.overlayImageBase64;
        const metrics = result.technicalMetrics;

        return (
          <Card key={result.imageId || index} className="border-primary/20 overflow-hidden">
            <CardHeader className="bg-muted/10 border-b">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <Eye className="h-5 w-5 text-primary" />
                    Analysis Result #{index + 1}: {result.filename || correspondingUpload?.file.name || 'Knee Image'}
                  </CardTitle>
                  <CardDescription>
                    Analyzed on {new Date(result.timestamp).toLocaleString()}
                  </CardDescription>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <p className="text-xs text-muted-foreground mb-0.5">AI Confidence</p>
                    <div className="flex items-center gap-2">
                      <Progress value={result.confidence} className="w-20" />
                      <span className="text-sm font-bold text-primary">{result.confidence}%</span>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleOpenReport(result)}
                    className="gap-1.5 ml-2"
                  >
                    <Printer className="h-3.5 w-3.5" />
                    Report
                  </Button>
                </div>
              </div>
            </CardHeader>

            <CardContent className="space-y-6 pt-6">
              {/* Medical Visual Results (3-column layout) */}
              <div>
                <h4 className="text-sm font-semibold mb-3 flex items-center gap-2 text-primary">
                  <Sparkles className="h-4 w-4" />
                  Medical Visual Results
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  {/* Original Image */}
                  <div className="border rounded-lg overflow-hidden bg-card text-center">
                    <div className="h-48 bg-black flex items-center justify-center p-1">
                      {originalSrc ? (
                        <img
                          src={originalSrc}
                          alt="Original Knee Scan"
                          className="max-h-48 max-w-full object-contain"
                        />
                      ) : (
                        <span className="text-xs text-muted-foreground">Original image not available</span>
                      )}
                    </div>
                    <div className="p-2.5 border-t bg-muted/20">
                      <p className="text-xs font-semibold">1. Original Knee Scan</p>
                      <p className="text-[11px] text-muted-foreground">Uploaded patient image</p>
                    </div>
                  </div>

                  {/* AI Segmentation Mask */}
                  <div className="border rounded-lg overflow-hidden bg-card text-center">
                    <div className="h-48 bg-black flex items-center justify-center p-1">
                      {maskSrc ? (
                        <img
                          src={maskSrc}
                          alt="AI Segmentation Mask"
                          className="max-h-48 max-w-full object-contain"
                        />
                      ) : (
                        <span className="text-xs text-muted-foreground">Segmentation mask not available</span>
                      )}
                    </div>
                    <div className="p-2.5 border-t bg-muted/20">
                      <p className="text-xs font-semibold">2. AI Segmentation Mask</p>
                      <p className="text-[11px] text-muted-foreground">U-Net predicted mask</p>
                    </div>
                  </div>

                  {/* AI Overlay Visualization */}
                  <div className="border rounded-lg overflow-hidden bg-card text-center">
                    <div className="h-48 bg-black flex items-center justify-center p-1">
                      {overlaySrc ? (
                        <img
                          src={overlaySrc}
                          alt="AI Overlay Visualization"
                          className="max-h-48 max-w-full object-contain"
                        />
                      ) : (
                        <span className="text-xs text-muted-foreground">Overlay visualization not available</span>
                      )}
                    </div>
                    <div className="p-2.5 border-t bg-muted/20">
                      <p className="text-xs font-semibold">3. AI Overlay Visualization</p>
                      <p className="text-[11px] text-muted-foreground">Composite segmented region</p>
                    </div>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Real AI Segmentation Metrics */}
              <div>
                <h4 className="text-sm font-semibold mb-3 flex items-center gap-2 text-primary">
                  <Layers className="h-4 w-4" />
                  Real AI Segmentation Metrics
                </h4>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="p-3 rounded-lg border bg-muted/20 text-center">
                    <p className="text-xs text-muted-foreground mb-1">Probability Mean</p>
                    <p className="text-lg font-bold text-foreground">
                      {typeof metrics?.probabilityMean === 'number'
                        ? metrics.probabilityMean.toFixed(4)
                        : 'N/A'}
                    </p>
                    <p className="text-[10px] text-primary font-medium mt-0.5">Confidence Metric</p>
                  </div>

                  <div className="p-3 rounded-lg border bg-muted/20 text-center">
                    <p className="text-xs text-muted-foreground mb-1">Mask Fraction</p>
                    <p className="text-lg font-bold text-foreground">
                      {typeof metrics?.maskFraction === 'number'
                        ? `${(metrics.maskFraction * 100).toFixed(2)}%`
                        : 'N/A'}
                    </p>
                    <p className="text-[10px] text-primary font-medium mt-0.5">Region Coverage</p>
                  </div>

                  <div className="p-3 rounded-lg border bg-muted/20 text-center">
                    <p className="text-xs text-muted-foreground mb-1">Mask Area</p>
                    <p className="text-lg font-bold text-foreground">
                      {typeof metrics?.maskAreaPixels === 'number'
                        ? metrics.maskAreaPixels.toLocaleString()
                        : 'N/A'}
                    </p>
                    <p className="text-[10px] text-primary font-medium mt-0.5">Segmented Pixels</p>
                  </div>

                  <div className="p-3 rounded-lg border bg-muted/20 text-center">
                    <p className="text-xs text-muted-foreground mb-1">Threshold</p>
                    <p className="text-lg font-bold text-foreground">
                      {typeof metrics?.threshold === 'number'
                        ? metrics.threshold.toFixed(2)
                        : '0.50'}
                    </p>
                    <p className="text-[10px] text-primary font-medium mt-0.5">Inference Cutoff</p>
                  </div>
                </div>
              </div>

              {/* AI-Assisted Findings */}
              {result.findings.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold mb-2 flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                    AI-Assisted Processing Findings
                  </h4>
                  <ul className="space-y-1 rounded-lg border bg-muted/10 p-3">
                    {result.findings.map((finding, idx) => (
                      <li key={idx} className="text-xs text-muted-foreground flex items-start gap-2">
                        <span className="text-primary mt-0.5 font-bold">•</span>
                        <span>{finding}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Action Button for Report */}
              <div className="flex justify-end pt-2">
                <Button
                  onClick={() => handleOpenReport(result)}
                  variant="outline"
                  className="gap-2"
                >
                  <FileText className="h-4 w-4 text-primary" />
                  Generate Patient Medical Result Report
                </Button>
              </div>
            </CardContent>
          </Card>
        );
      })}

      {/* Patient Medical Result Report Modal */}
      <PatientMedicalReportModal
        isOpen={isReportModalOpen}
        onClose={() => setIsReportModalOpen(false)}
        result={selectedResultForReport}
        uploadedImage={
          selectedResultForReport
            ? uploadedImages.find(img => img.id === selectedResultForReport.imageId)
            : undefined
        }
        patientInfo={patientInfo}
      />
    </div>
  );
}
