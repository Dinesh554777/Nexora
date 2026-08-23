import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/Dialog';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Printer, FileText, AlertTriangle } from 'lucide-react';
import { ImageAnalysisResult, UploadedImage } from '@/types';
import { PatientInfo } from '@/components/implant/PatientInfoForm';
import { computeMetricDifferences } from './MetricComparisonTable';

interface PrintComparisonModalProps {
  isOpen: boolean;
  onClose: () => void;
  previousResult: ImageAnalysisResult;
  currentResult: ImageAnalysisResult;
  previousImage?: UploadedImage;
  currentImage?: UploadedImage;
  previousDate?: string;
  currentDate?: string;
  patientInfo?: PatientInfo;
}

export function PrintComparisonModal({
  isOpen,
  onClose,
  previousResult,
  currentResult,
  previousImage,
  currentImage,
  previousDate,
  currentDate,
  patientInfo,
}: PrintComparisonModalProps) {
  const [printing, setPrinting] = useState(false);

  const reportId = `NXR-CMP-${Date.now().toString(36).toUpperCase()}`;
  const generatedAt = new Date().toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  const patientNameDisplay = patientInfo?.patientName?.trim() || 'Not provided';
  const patientIdDisplay = patientInfo?.patientId?.trim() || 'Not provided';
  const ageDisplay = patientInfo?.age?.trim() ? `${patientInfo.age} yrs` : 'Not provided';
  const sexDisplay =
    patientInfo?.sex === 'M'
      ? 'Male'
      : patientInfo?.sex === 'F'
      ? 'Female'
      : patientInfo?.sex?.trim() || 'Not provided';

  const prevOriginal = previousResult.originalImageBase64 || previousImage?.preview;
  const currOriginal = currentResult.originalImageBase64 || currentImage?.preview;
  const prevMask = previousResult.maskImageBase64;
  const currMask = currentResult.maskImageBase64;
  const prevOverlay = previousResult.overlayImageBase64;
  const currOverlay = currentResult.overlayImageBase64;

  const differences = computeMetricDifferences(previousResult, currentResult);
  const anyChanged = differences.some(d => d.differenceType === 'positive' || d.differenceType === 'negative');
  const technicalSummary = anyChanged
    ? 'The comparison shows differences between the previous and current AI-generated segmentation outputs. Changes in technical metrics are displayed above for clinical review.'
    : 'No difference was observed in the displayed technical comparison metrics.';

  const handlePrint = () => {
    setPrinting(true);

    const printWindow = window.open('', '_blank');
    if (!printWindow) {
      setPrinting(false);
      alert('Please allow popups to print the Progress Comparison Report.');
      return;
    }

    const printHtml = `
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="utf-8" />
        <title>Nexora Progress View Comparison - ${reportId}</title>
        <style>
          @page {
            size: A4 portrait;
            margin: 12mm;
          }
          * {
            box-sizing: border-box;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
          }
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            color: #0f172a;
            background: #ffffff;
            margin: 0;
            padding: 0;
            font-size: 12px;
            line-height: 1.4;
          }
          .report-container {
            max-width: 800px;
            margin: 0 auto;
          }
          .report-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            border-bottom: 2px solid #0284c7;
            padding-bottom: 10px;
            margin-bottom: 14px;
          }
          .brand-title {
            font-size: 18px;
            font-weight: 800;
            color: #0369a1;
            margin: 0 0 2px 0;
          }
          .brand-subtitle {
            font-size: 10px;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin: 0;
          }
          .doc-title-box {
            text-align: right;
          }
          .doc-title {
            font-size: 14px;
            font-weight: 700;
            color: #0f172a;
            margin: 0 0 2px 0;
          }
          .meta-text {
            font-size: 10px;
            color: #475569;
            margin: 1px 0;
          }
          .section {
            margin-bottom: 14px;
            page-break-inside: avoid;
          }
          .section-title {
            font-size: 12px;
            font-weight: 700;
            color: #0369a1;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 3px;
            margin: 0 0 8px 0;
          }
          .grid-4 {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 8px;
          }
          .grid-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
          }
          .info-card {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 4px;
            padding: 6px 10px;
          }
          .info-label {
            font-size: 9px;
            font-weight: 600;
            color: #64748b;
            text-transform: uppercase;
          }
          .info-value {
            font-size: 12px;
            font-weight: 600;
            color: #0f172a;
          }
          .visual-box {
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            overflow: hidden;
            text-align: center;
          }
          .visual-box-header {
            font-size: 10px;
            font-weight: 700;
            padding: 4px 8px;
            color: #ffffff;
            display: flex;
            justify-content: space-between;
          }
          .bg-prev { background: #334155; }
          .bg-curr { background: #0284c7; }
          .visual-img-wrap {
            width: 100%;
            height: 140px;
            background: #000000;
            display: flex;
            align-items: center;
            justify-content: center;
          }
          .visual-img {
            max-width: 100%;
            max-height: 140px;
            object-fit: contain;
          }
          .visual-caption {
            font-size: 10px;
            color: #475569;
            padding: 4px;
            background: #f8fafc;
            border-top: 1px solid #e2e8f0;
          }
          table {
            width: 100%;
            border-collapse: collapse;
            font-size: 11px;
          }
          th, td {
            padding: 6px 10px;
            border-bottom: 1px solid #e2e8f0;
          }
          th {
            background: #f1f5f9;
            font-weight: 700;
            color: #334155;
          }
          .text-right { text-align: right; }
          .font-mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }
          .summary-box {
            background: #f0f9ff;
            border-left: 3px solid #0284c7;
            padding: 8px 12px;
            border-radius: 0 4px 4px 0;
            font-size: 11px;
            color: #0c4a6e;
          }
          .disclaimer-box {
            background: #fffbeb;
            border: 1px solid #fde68a;
            border-left: 4px solid #f59e0b;
            padding: 8px 10px;
            border-radius: 4px;
            font-size: 10px;
            color: #92400e;
            margin-top: 10px;
            page-break-inside: avoid;
          }
          .signoff-section {
            margin-top: 18px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            padding-top: 10px;
            border-top: 1px solid #e2e8f0;
            page-break-inside: avoid;
          }
          .sig-line {
            border-bottom: 1px solid #475569;
            height: 26px;
            margin-bottom: 3px;
          }
          .sig-label {
            font-size: 9px;
            color: #64748b;
            text-transform: uppercase;
          }
          .footer {
            margin-top: 14px;
            text-align: center;
            font-size: 9px;
            color: #94a3b8;
            border-top: 1px solid #f1f5f9;
            padding-top: 6px;
          }
          @media print {
            body { margin: 0; padding: 0; }
            .report-container { max-width: 100%; }
          }
        </style>
      </head>
      <body>
        <div class="report-container">
          <!-- Header -->
          <div class="report-header">
            <div>
              <h1 class="brand-title">NEXORA PROGRESS VIEW</h1>
              <p class="brand-subtitle">Previous vs Current AI Scan Comparison Report</p>
            </div>
            <div class="doc-title-box">
              <div class="doc-title">AI SCAN COMPARISON</div>
              <div class="meta-text"><strong>Report ID:</strong> ${reportId}</div>
              <div class="meta-text"><strong>Generated:</strong> ${generatedAt}</div>
            </div>
          </div>

          <!-- Patient & Timeline Info -->
          <div class="section">
            <div class="section-title">Patient & Scan Information</div>
            <div class="grid-4">
              <div class="info-card">
                <div class="info-label">Patient Name</div>
                <div class="info-value">${patientNameDisplay}</div>
              </div>
              <div class="info-card">
                <div class="info-label">Patient ID</div>
                <div class="info-value">${patientIdDisplay}</div>
              </div>
              <div class="info-card">
                <div class="info-label">Age</div>
                <div class="info-value">${ageDisplay}</div>
              </div>
              <div class="info-card">
                <div class="info-label">Sex / Gender</div>
                <div class="info-value">${sexDisplay}</div>
              </div>
            </div>
            <div class="grid-2" style="margin-top: 6px;">
              <div class="info-card">
                <div class="info-label">Previous Scan (Baseline)</div>
                <div class="info-value">${previousDate || 'Not specified'} — ${previousResult.filename || previousImage?.file.name || 'Scan A'}</div>
              </div>
              <div class="info-card">
                <div class="info-label">Current Scan (Follow-up)</div>
                <div class="info-value">${currentDate || 'Not specified'} — ${currentResult.filename || currentImage?.file.name || 'Scan B'}</div>
              </div>
            </div>
          </div>

          <!-- Side by Side Visuals -->
          <div class="section">
            <div class="section-title">Side-by-Side Visual Comparison</div>
            
            <!-- Original Scans -->
            <p style="font-size:10px; font-weight:700; margin:4px 0; color:#334155;">1. Original Knee X-Rays</p>
            <div class="grid-2" style="margin-bottom: 8px;">
              <div class="visual-box">
                <div class="visual-box-header bg-prev">
                  <span>PREVIOUS SCAN</span>
                  <span>${previousDate || 'Baseline'}</span>
                </div>
                <div class="visual-img-wrap">
                  ${prevOriginal ? `<img src="${prevOriginal}" class="visual-img" />` : '<span style="color:#64748b;">Image unavailable</span>'}
                </div>
              </div>
              <div class="visual-box">
                <div class="visual-box-header bg-curr">
                  <span>CURRENT SCAN</span>
                  <span>${currentDate || 'Follow-up'}</span>
                </div>
                <div class="visual-img-wrap">
                  ${currOriginal ? `<img src="${currOriginal}" class="visual-img" />` : '<span style="color:#64748b;">Image unavailable</span>'}
                </div>
              </div>
            </div>

            <!-- Segmentation Masks -->
            <p style="font-size:10px; font-weight:700; margin:4px 0; color:#334155;">2. AI Segmentation Masks</p>
            <div class="grid-2" style="margin-bottom: 8px;">
              <div class="visual-box">
                <div class="visual-box-header bg-prev">
                  <span>PREVIOUS AI MASK</span>
                  <span>U-Net Mask</span>
                </div>
                <div class="visual-img-wrap">
                  ${prevMask ? `<img src="${prevMask}" class="visual-img" />` : '<span style="color:#64748b;">Mask unavailable</span>'}
                </div>
              </div>
              <div class="visual-box">
                <div class="visual-box-header bg-curr">
                  <span>CURRENT AI MASK</span>
                  <span>U-Net Mask</span>
                </div>
                <div class="visual-img-wrap">
                  ${currMask ? `<img src="${currMask}" class="visual-img" />` : '<span style="color:#64748b;">Mask unavailable</span>'}
                </div>
              </div>
            </div>

            <!-- Overlays -->
            <p style="font-size:10px; font-weight:700; margin:4px 0; color:#334155;">3. AI Overlay Visualizations</p>
            <div class="grid-2" style="margin-bottom: 8px;">
              <div class="visual-box">
                <div class="visual-box-header bg-prev">
                  <span>PREVIOUS AI OVERLAY</span>
                  <span>Composite Map</span>
                </div>
                <div class="visual-img-wrap">
                  ${prevOverlay ? `<img src="${prevOverlay}" class="visual-img" />` : '<span style="color:#64748b;">Overlay unavailable</span>'}
                </div>
              </div>
              <div class="visual-box">
                <div class="visual-box-header bg-curr">
                  <span>CURRENT AI OVERLAY</span>
                  <span>Composite Map</span>
                </div>
                <div class="visual-img-wrap">
                  ${currOverlay ? `<img src="${currOverlay}" class="visual-img" />` : '<span style="color:#64748b;">Overlay unavailable</span>'}
                </div>
              </div>
            </div>
          </div>

          <!-- Real Metric Comparison Table -->
          <div class="section">
            <div class="section-title">Real AI Metric Comparison</div>
            <table>
              <thead>
                <tr>
                  <th>Metric</th>
                  <th class="text-right">Previous Scan</th>
                  <th class="text-right">Current Scan</th>
                  <th class="text-right">Difference (Current - Previous)</th>
                </tr>
              </thead>
              <tbody>
                ${differences.map(d => `
                  <tr>
                    <td><strong>${d.metricName}</strong></td>
                    <td class="text-right font-mono">${d.previousFormatted}</td>
                    <td class="text-right font-mono">${d.currentFormatted}</td>
                    <td class="text-right font-mono" style="font-weight:600;">${d.differenceFormatted}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>

          <!-- Technical Comparison Summary -->
          <div class="section">
            <div class="section-title">Technical Comparison Summary</div>
            <div class="summary-box">
              ${technicalSummary}
            </div>
          </div>

          <!-- Clinical Safety Disclaimer -->
          <div class="disclaimer-box">
            <strong>Clinical Safety Disclaimer:</strong> This comparison presents differences between AI-generated image analysis outputs from two scans. It is intended to support clinical review and does not independently diagnose disease progression, improvement, or any medical condition. Final interpretation must be made by a qualified healthcare professional.
          </div>

          <!-- Reviewer Sign-off -->
          <div class="signoff-section">
            <div>
              <div class="sig-line"></div>
              <div class="sig-label">Reviewing Clinician Signature</div>
            </div>
            <div>
              <div class="sig-line"></div>
              <div class="sig-label">Clinical Review Date & Findings</div>
            </div>
          </div>

          <div class="footer">
            Nexora AI Platform v0.1.0 • Progress View Comparison Report • Confidential Medical Record
          </div>
        </div>
      </body>
      </html>
    `;

    printWindow.document.write(printHtml);
    printWindow.document.close();

    setTimeout(() => {
      printWindow.focus();
      printWindow.print();
      setPrinting(false);
    }, 400);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto p-6">
        <DialogHeader className="border-b pb-4">
          <DialogTitle className="text-xl font-bold flex items-center gap-2 text-primary">
            <FileText className="h-5 w-5" />
            Print Nexora Progress View Comparison Report
          </DialogTitle>
          <DialogDescription>
            Preview and print the side-by-side comparison of Previous vs Current AI Scan analyses.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="rounded-lg border bg-muted/20 p-3 flex justify-between text-xs">
            <div>
              <span className="text-muted-foreground">Patient:</span> <span className="font-semibold">{patientNameDisplay}</span> {patientIdDisplay !== 'Not provided' && `(ID: ${patientIdDisplay})`}
            </div>
            <div>
              <span className="text-muted-foreground">Report ID:</span> <span className="font-mono font-semibold">{reportId}</span>
            </div>
          </div>

          <div className="rounded-lg border bg-muted/30 p-3 text-xs leading-relaxed">
            <p className="font-semibold text-primary mb-1">Technical Summary</p>
            <p className="text-muted-foreground">{technicalSummary}</p>
          </div>

          <Alert className="border-amber-200 bg-amber-50 dark:bg-amber-950/40">
            <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400" />
            <AlertDescription className="text-xs text-amber-800 dark:text-amber-300">
              <strong>Clinical Safety Disclaimer:</strong> This comparison presents differences between AI-generated image analysis outputs from two scans. It is intended to support clinical review and does not independently diagnose disease progression, improvement, or any medical condition.
            </AlertDescription>
          </Alert>
        </div>

        <DialogFooter className="border-t pt-4 flex-row justify-end gap-2">
          <Button variant="outline" onClick={onClose} disabled={printing}>
            Close
          </Button>
          <Button onClick={handlePrint} disabled={printing} className="gap-2">
            <Printer className="h-4 w-4" />
            {printing ? 'Preparing Print...' : 'Print Comparison Report'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

