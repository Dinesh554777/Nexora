import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Progress } from '@/components/ui/progress';
import { AlertTriangle, CheckCircle2, Eye, Activity, Printer, ReceiptText } from 'lucide-react';
import { BillingSummary, ImageAnalysisResult, UploadedImage } from '@/types';

interface AnalysisResultsProps {
  results: ImageAnalysisResult[];
  uploadedImages?: UploadedImage[];
}

const BILLING_CONFIG = {
  baseFee: 180,
  perImageFee: 45,
  oaReviewFee: 60,
  taxRate: 0.08,
  currency: 'USD',
};

export function AnalysisResults({ results, uploadedImages = [] }: AnalysisResultsProps) {
  if (results.length === 0) {
    return null;
  }

  const billingSummary: BillingSummary = (() => {
    const serviceCount = uploadedImages.length || results.length;
    const oaCases = results.filter(result => result.oaIndicators?.present).length;
    const analysisFee = BILLING_CONFIG.baseFee;
    const imageFee = serviceCount * BILLING_CONFIG.perImageFee;
    const oaReviewFee = oaCases * BILLING_CONFIG.oaReviewFee;
    const subtotal = analysisFee + imageFee + oaReviewFee;
    const tax = Number((subtotal * BILLING_CONFIG.taxRate).toFixed(2));

    return {
      analysisFee,
      imageFee,
      oaReviewFee,
      subtotal,
      tax,
      total: subtotal + tax,
      currency: BILLING_CONFIG.currency,
      serviceCount,
      oaCases,
    };
  })();

  const getSeverityColor = (severity: 'low' | 'medium' | 'high') => {
    switch (severity) {
      case 'low': return 'bg-green-500';
      case 'medium': return 'bg-yellow-500';
      case 'high': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getOASeverityColor = (severity: 'none' | 'mild' | 'moderate' | 'severe') => {
    switch (severity) {
      case 'none': return 'text-green-600';
      case 'mild': return 'text-yellow-600';
      case 'moderate': return 'text-orange-600';
      case 'severe': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const generatePrintableReport = () => {
    const timestamp = new Date().toLocaleString();
    const imageRows = results.map((result, index) => {
      const findings = result.findings.map(finding => `<li>${finding}</li>`).join('');
      const abnormalRegions = result.abnormalRegions.map((region) => `
        <tr>
          <td>${region.region}</td>
          <td>${region.severity}</td>
          <td>${region.description}</td>
        </tr>
      `).join('');
      const measurements = result.measurements ? `
        <div class="grid">
          ${result.measurements.meniscusThickness ? `<div class="field"><div class="label">Meniscus Thickness</div><div class="value">${result.measurements.meniscusThickness} mm</div></div>` : ''}
          ${result.measurements.jointSpaceWidth ? `<div class="field"><div class="label">Joint Space Width</div><div class="value">${result.measurements.jointSpaceWidth} mm</div></div>` : ''}
        </div>
      ` : '';
      const oaSection = result.oaIndicators ? `
        <div class="section">
          <h3>OA assessment</h3>
          <p><strong>Present:</strong> ${result.oaIndicators.present ? 'Yes' : 'No'}</p>
          <p><strong>Severity:</strong> ${result.oaIndicators.severity}</p>
          <ul>${result.oaIndicators.observations.map(obs => `<li>${obs}</li>`).join('')}</ul>
        </div>
      ` : '';

      return `
        <div class="section">
          <h2>Analysis Result ${index + 1}</h2>
          <p><strong>Timestamp:</strong> ${new Date(result.timestamp).toLocaleString()}</p>
          <p><strong>Confidence:</strong> ${result.confidence}%</p>
          <h3>Findings</h3>
          <ul>${findings}</ul>
          ${abnormalRegions ? `
            <h3>Abnormal regions</h3>
            <table>
              <thead><tr><th>Region</th><th>Severity</th><th>Description</th></tr></thead>
              <tbody>${abnormalRegions}</tbody>
            </table>
          ` : ''}
          ${measurements}
          ${oaSection}
        </div>
      `;
    }).join('');

    const printWindow = window.open('', '_blank');
    if (!printWindow) {
      return;
    }

    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>Nexora AI Analysis Report</title>
        <style>
          body { font-family: Arial, sans-serif; max-width: 1000px; margin: 32px auto; padding: 24px; color: #111827; }
          h1 { color: #0f172a; border-bottom: 3px solid #0f172a; padding-bottom: 10px; }
          h2 { color: #1d4ed8; margin-top: 20px; }
          h3 { margin-top: 18px; }
          .section { margin: 18px 0; padding: 16px; border: 1px solid #e5e7eb; border-radius: 12px; background: #f8fafc; }
          .grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
          .field { padding: 12px; background: white; border: 1px solid #e2e8f0; border-radius: 8px; }
          .label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; color: #64748b; }
          .value { margin-top:6px; font-size: 18px; font-weight: 600; }
          table { width: 100%; border-collapse: collapse; margin-top: 10px; }
          th, td { padding: 10px; border-bottom: 1px solid #e5e7eb; text-align: left; vertical-align: top; }
          th { background: #e2e8f0; }
          .billing { margin-top: 24px; border: 1px solid #dbeafe; border-radius: 12px; background: #eff6ff; padding: 18px; }
          .total { font-size: 28px; font-weight: 700; }
          .disclaimer { margin-top: 28px; padding: 14px; background: #fef3c7; border-left: 4px solid #f59e0b; }
          @media print { body { margin: 0; padding: 24px; } }
        </style>
      </head>
      <body>
        <h1>Nexora AI Analysis Report</h1>
        <p><strong>Generated:</strong> ${timestamp}</p>
        <div class="section">
          <h2>Clinical Summary</h2>
          <div class="grid">
            <div class="field"><div class="label">Images analyzed</div><div class="value">${uploadedImages.length || results.length}</div></div>
            <div class="field"><div class="label">OA findings</div><div class="value">${results.filter(result => result.oaIndicators?.present).length}</div></div>
          </div>
        </div>
        ${imageRows}
        <div class="billing">
          <h2>Billing Summary</h2>
          <p><strong>Service count:</strong> ${billingSummary.serviceCount}</p>
          <p><strong>Analysis fee:</strong> $${billingSummary.analysisFee.toFixed(2)}</p>
          <p><strong>Image fee:</strong> $${billingSummary.imageFee.toFixed(2)}</p>
          <p><strong>OA review fee:</strong> $${billingSummary.oaReviewFee.toFixed(2)}</p>
          <p><strong>Subtotal:</strong> $${billingSummary.subtotal.toFixed(2)}</p>
          <p><strong>Tax:</strong> $${billingSummary.tax.toFixed(2)}</p>
          <p class="total"><strong>Total:</strong> $${billingSummary.total.toFixed(2)}</p>
        </div>
        <div class="disclaimer">
          <strong>Clinical note:</strong> This report is intended to support clinical review and does not replace professional medical diagnosis.
        </div>
      </body>
      </html>
    `);
    printWindow.document.close();
    setTimeout(() => printWindow.focus(), 200);
    setTimeout(() => printWindow.print(), 500);
  };

  return (
    <div className="space-y-6">
      <Alert className="border-orange-200 bg-orange-50 dark:bg-orange-950 dark:border-orange-900">
        <AlertTriangle className="h-5 w-5 text-orange-600 dark:text-orange-400" />
        <AlertTitle className="text-orange-800 dark:text-orange-200">
          AI-Assisted Analysis
        </AlertTitle>
        <AlertDescription className="text-orange-700 dark:text-orange-300">
          AI-assisted analysis is intended to support clinical decision-making and does not replace professional medical diagnosis. All findings require review and confirmation by a qualified healthcare professional.
        </AlertDescription>
      </Alert>

      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-sm text-muted-foreground">Analysis summary</p>
          <p className="text-lg font-semibold">{results.length} image{results.length !== 1 ? 's' : ''} reviewed</p>
        </div>
        <Button variant="outline" onClick={generatePrintableReport} className="gap-2">
          <Printer className="h-4 w-4" />
          Printable Report
        </Button>
      </div>

      <Card className="border-primary/20">
        <CardHeader>
          <div className="flex items-center justify-between gap-3">
            <div>
              <CardTitle className="flex items-center gap-2">
                <ReceiptText className="h-5 w-5 text-primary" />
                Billing Summary
              </CardTitle>
              <CardDescription>Charges are based on the actual study workflow and image count.</CardDescription>
            </div>
            <div className="text-right">
              <p className="text-xs text-muted-foreground uppercase tracking-wide">Total</p>
              <p className="text-2xl font-bold text-primary">${billingSummary.total.toFixed(2)}</p>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-lg border bg-muted/30 p-3">
              <p className="text-xs text-muted-foreground">Study fee</p>
              <p className="text-lg font-semibold">${billingSummary.analysisFee.toFixed(2)}</p>
            </div>
            <div className="rounded-lg border bg-muted/30 p-3">
              <p className="text-xs text-muted-foreground">Image review</p>
              <p className="text-lg font-semibold">${billingSummary.imageFee.toFixed(2)}</p>
            </div>
            <div className="rounded-lg border bg-muted/30 p-3">
              <p className="text-xs text-muted-foreground">OA assessment</p>
              <p className="text-lg font-semibold">${billingSummary.oaReviewFee.toFixed(2)}</p>
            </div>
            <div className="rounded-lg border bg-muted/30 p-3">
              <p className="text-xs text-muted-foreground">Tax</p>
              <p className="text-lg font-semibold">${billingSummary.tax.toFixed(2)}</p>
            </div>
          </div>
          <Separator />
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Service count</span>
            <span className="font-medium">{billingSummary.serviceCount}</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">OA cases reviewed</span>
            <span className="font-medium">{billingSummary.oaCases}</span>
          </div>
        </CardContent>
      </Card>

      {results.map((result, index) => (
        <Card key={result.imageId} className="border-primary/20">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Eye className="h-5 w-5 text-primary" />
                  Analysis Result #{index + 1}
                </CardTitle>
                <CardDescription>
                  {new Date(result.timestamp).toLocaleString()}
                </CardDescription>
              </div>
              <div className="text-right">
                <p className="text-sm text-muted-foreground mb-1">Confidence</p>
                <div className="flex items-center gap-2">
                  <Progress value={result.confidence} className="w-24" />
                  <span className="text-lg font-bold text-primary">{result.confidence}%</span>
                </div>
              </div>
            </div>
          </CardHeader>

          <CardContent className="space-y-4">
            {result.findings.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold mb-2 flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                  AI-Assisted Findings
                </h4>
                <ul className="space-y-1">
                  {result.findings.map((finding, idx) => (
                    <li key={idx} className="text-sm text-muted-foreground flex items-start gap-2">
                      <span className="text-primary mt-0.5">•</span>
                      <span>{finding}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <Separator />

            {result.abnormalRegions.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold mb-3">Possible Abnormal Regions</h4>
                <div className="space-y-2">
                  {result.abnormalRegions.map((region, idx) => (
                    <div key={idx} className="p-3 rounded-lg bg-muted/50 border">
                      <div className="flex items-start justify-between mb-1">
                        <p className="font-medium text-sm">{region.region}</p>
                        <Badge variant="outline" className={getSeverityColor(region.severity)}>
                          {region.severity}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">{region.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {result.measurements && (
              <>
                <Separator />
                <div>
                  <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
                    <Activity className="h-4 w-4 text-primary" />
                    Detected Measurements
                  </h4>
                  <div className="grid grid-cols-2 gap-3">
                    {result.measurements.meniscusThickness && (
                      <div className="p-3 rounded-lg bg-muted/30">
                        <p className="text-xs text-muted-foreground mb-1">Meniscus Thickness</p>
                        <p className="text-xl font-bold">{result.measurements.meniscusThickness} mm</p>
                      </div>
                    )}
                    {result.measurements.jointSpaceWidth && (
                      <div className="p-3 rounded-lg bg-muted/30">
                        <p className="text-xs text-muted-foreground mb-1">Joint Space Width</p>
                        <p className="text-xl font-bold">{result.measurements.jointSpaceWidth} mm</p>
                      </div>
                    )}
                  </div>
                </div>
              </>
            )}

            {result.oaIndicators && (
              <>
                <Separator />
                <div>
                  <h4 className="text-sm font-semibold mb-3">Osteoarthritis Indicators</h4>
                  <div className="p-4 rounded-lg bg-muted/30 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">OA Indicators Present</span>
                      <Badge variant={result.oaIndicators.present ? 'destructive' : 'outline'}>
                        {result.oaIndicators.present ? 'Yes' : 'No'}
                      </Badge>
                    </div>
                    {result.oaIndicators.present && (
                      <>
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium">Severity Assessment</span>
                          <span className={`text-sm font-bold ${getOASeverityColor(result.oaIndicators.severity)}`}>
                            {result.oaIndicators.severity.charAt(0).toUpperCase() + result.oaIndicators.severity.slice(1)}
                          </span>
                        </div>
                        <Separator />
                        <div>
                          <p className="text-xs text-muted-foreground mb-2">Observations:</p>
                          <ul className="space-y-1">
                            {result.oaIndicators.observations.map((obs, idx) => (
                              <li key={idx} className="text-sm text-muted-foreground flex items-start gap-2">
                                <span className="text-primary mt-0.5">•</span>
                                <span>{obs}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              </>
            )}

            <Alert className="bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-900">
              <AlertDescription className="text-sm text-blue-800 dark:text-blue-200">
                <strong>Note:</strong> These findings require clinical review and confirmation. Consult with a qualified healthcare professional for diagnosis and treatment planning.
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
