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
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Printer,
  FileText,
  AlertTriangle,
  CheckCircle2,
  Activity,
  Layers,
  Sparkles,
} from 'lucide-react';
import { ImageAnalysisResult, UploadedImage } from '@/types';
import { PatientInfo } from '@/components/implant/PatientInfoForm';

interface PatientMedicalReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  result: ImageAnalysisResult | null;
  uploadedImage?: UploadedImage;
  patientInfo?: PatientInfo;
}

export function PatientMedicalReportModal({
  isOpen,
  onClose,
  result,
  uploadedImage,
  patientInfo,
}: PatientMedicalReportModalProps) {
  const [printing, setPrinting] = useState(false);

  if (!result) {
    return null;
  }

  // Deterministic or clean report ID
  const reportId = `NXR-RPT-${result.imageId ? result.imageId.slice(-6).toUpperCase() : Date.now().toString(36).toUpperCase()}`;
  const generatedAt = new Date();
  const formattedDate = generatedAt.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
  const scanDate = new Date(result.timestamp).toLocaleString('en-US', {
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

  const originalImageSrc = result.originalImageBase64 || uploadedImage?.preview;
  const maskImageSrc = result.maskImageBase64;
  const overlayImageSrc = result.overlayImageBase64;

  const metrics = result.technicalMetrics;
  const hasProbabilityMean = typeof metrics?.probabilityMean === 'number';
  const hasMaskArea = typeof metrics?.maskAreaPixels === 'number';
  const hasMaskFraction = typeof metrics?.maskFraction === 'number';
  const hasThreshold = typeof metrics?.threshold === 'number';

  const oa = result.oaAssessment;
  const isOA = oa?.classification === 'OA';
  const oaConfidencePct = oa ? Math.round(oa.confidence * 100) : null;

  const handlePrint = () => {
    setPrinting(true);

    const printWindow = window.open('', '_blank');
    if (!printWindow) {
      setPrinting(false);
      alert('Please allow popups to print the Patient Medical Result Report.');
      return;
    }

    const printHtml = `
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="utf-8" />
        <title>Patient Medical Result Report - ${reportId}</title>
        <style>
          @page {
            size: A4 portrait;
            margin: 15mm;
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
            font-size: 13px;
            line-height: 1.5;
          }
          .report-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 10px 0;
          }
          .report-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            border-bottom: 2px solid #0284c7;
            padding-bottom: 12px;
            margin-bottom: 18px;
          }
          .brand-title {
            font-size: 20px;
            font-weight: 800;
            color: #0369a1;
            letter-spacing: -0.02em;
            margin: 0 0 2px 0;
          }
          .brand-subtitle {
            font-size: 11px;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin: 0;
          }
          .doc-title-box {
            text-align: right;
          }
          .doc-title {
            font-size: 15px;
            font-weight: 700;
            color: #0f172a;
            margin: 0 0 4px 0;
            letter-spacing: 0.02em;
          }
          .meta-text {
            font-size: 11px;
            color: #475569;
            margin: 2px 0;
          }
          .status-badge {
            display: inline-block;
            background-color: #ecfdf5;
            color: #047857;
            border: 1px solid #a7f3d0;
            padding: 2px 8px;
            border-radius: 9999px;
            font-size: 11px;
            font-weight: 600;
            margin-top: 4px;
          }
          .section {
            margin-bottom: 18px;
            page-break-inside: avoid;
          }
          .section-title {
            font-size: 13px;
            font-weight: 700;
            color: #0369a1;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 4px;
            margin: 0 0 10px 0;
          }
          .grid-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
          }
          .grid-4 {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
          }
          .grid-3 {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
          }
          .info-card {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 8px 12px;
          }
          .info-label {
            font-size: 10px;
            font-weight: 600;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 2px;
          }
          .info-value {
            font-size: 13px;
            font-weight: 600;
            color: #0f172a;
          }
          .metric-card {
            background: #f0f9ff;
            border: 1px solid #bae6fd;
            border-radius: 6px;
            padding: 10px;
            text-align: center;
          }
          .metric-label {
            font-size: 10px;
            font-weight: 600;
            color: #0369a1;
            text-transform: uppercase;
            margin-bottom: 4px;
          }
          .metric-value {
            font-size: 16px;
            font-weight: 700;
            color: #0c4a6e;
          }
          .metric-subtitle {
            font-size: 10px;
            color: #64748b;
            margin-top: 2px;
          }
          .visual-box {
            background: #f8fafc;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            overflow: hidden;
            text-align: center;
          }
          .visual-img-wrap {
            width: 100%;
            height: 180px;
            background: #000000;
            display: flex;
            align-items: center;
            justify-content: center;
          }
          .visual-img {
            max-width: 100%;
            max-height: 180px;
            object-fit: contain;
          }
          .visual-caption {
            font-size: 11px;
            font-weight: 600;
            color: #334155;
            padding: 6px 8px;
            background: #f1f5f9;
            border-top: 1px solid #e2e8f0;
          }
          .summary-box {
            background: #f8fafc;
            border-left: 3px solid #0284c7;
            padding: 10px 14px;
            border-radius: 0 6px 6px 0;
            font-size: 12px;
            color: #1e293b;
          }
          .disclaimer-box {
            background: #fffbeb;
            border: 1px solid #fde68a;
            border-left: 4px solid #f59e0b;
            padding: 10px 12px;
            border-radius: 4px;
            font-size: 11px;
            color: #92400e;
            margin-top: 14px;
            page-break-inside: avoid;
          }
          .disclaimer-title {
            font-weight: 700;
            margin-bottom: 2px;
          }
          .signoff-section {
            margin-top: 24px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 40px;
            padding-top: 12px;
            border-top: 1px solid #e2e8f0;
            page-break-inside: avoid;
          }
          .sig-line {
            border-bottom: 1px solid #475569;
            height: 32px;
            margin-bottom: 4px;
          }
          .sig-label {
            font-size: 10px;
            color: #64748b;
            text-transform: uppercase;
          }
          .footer {
            margin-top: 18px;
            text-align: center;
            font-size: 10px;
            color: #94a3b8;
            border-top: 1px solid #f1f5f9;
            padding-top: 8px;
          }
          @media print {
            body { margin: 0; padding: 0; }
            .report-container { max-width: 100%; }
          }
        </style>
      </head>
      <body>
        <div class="report-container">
          <!-- Report Header -->
          <div class="report-header">
            <div>
              <h1 class="brand-title">NEXORA MEDICAL AI</h1>
              <p class="brand-subtitle">Orthopedic Imaging & Analysis Platform</p>
            </div>
            <div class="doc-title-box">
              <div class="doc-title">PATIENT MEDICAL RESULT REPORT</div>
              <div class="meta-text"><strong>Report ID:</strong> ${reportId}</div>
              <div class="meta-text"><strong>Generated:</strong> ${formattedDate}</div>
              <span class="status-badge">✓ Analysis Status: Completed</span>
            </div>
          </div>

          <!-- Patient Information -->
          <div class="section">
            <div class="section-title">Patient Demographics</div>
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
            <div class="grid-2" style="margin-top: 8px;">
              <div class="info-card">
                <div class="info-label">Scan / Analysis Date</div>
                <div class="info-value">${scanDate}</div>
              </div>
              <div class="info-card">
                <div class="info-label">Image Source File</div>
                <div class="info-value">${result.filename || uploadedImage?.file.name || 'knee_image.png'}</div>
              </div>
            </div>
          </div>

          <!-- OA Assessment Verdict -->
          <div class="section">
            <div class="section-title">OA Assessment</div>
            ${oa ? `
            <div style="
              border-radius: 8px;
              border: 2px solid ${isOA ? '#fca5a5' : '#86efac'};
              background: ${isOA ? '#fef2f2' : '#f0fdf4'};
              padding: 16px 20px;
              margin-bottom: 12px;
            ">
              <div style="display:flex; align-items:center; justify-content:space-between; gap:16px; margin-bottom:12px;">
                <div>
                  <div style="font-size:11px; font-weight:600; color:#64748b; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:4px;">
                    AI OA Assessment Result
                  </div>
                  <div style="font-size:22px; font-weight:800; color:${isOA ? '#b91c1c' : '#15803d'}; letter-spacing:-0.02em;">
                    ${isOA ? 'OA DETECTED' : 'NO OA FEATURES DETECTED'}
                  </div>
                  <div style="font-size:12px; color:#475569; margin-top:3px;">
                    ${isOA ? 'This patient shows osteoarthritis features.' : 'This patient shows no significant OA features.'}
                  </div>
                </div>
                <div style="text-align:right;">
                  <div style="
                    display:inline-block;
                    background:${isOA ? '#fee2e2' : '#dcfce7'};
                    color:${isOA ? '#b91c1c' : '#15803d'};
                    border:1px solid ${isOA ? '#fca5a5' : '#86efac'};
                    border-radius:9999px;
                    padding:4px 14px;
                    font-size:13px;
                    font-weight:700;
                    margin-bottom:6px;
                  ">${isOA ? 'OA Patient' : 'Non-OA Patient'}</div>
                  ${oa.severity !== 'None' ? `<div style="font-size:11px; color:#475569;">Severity: <strong>${oa.severity}</strong></div>` : ''}
                  <div style="font-size:11px; color:#475569; margin-top:4px;">Confidence: <strong>${oaConfidencePct}%</strong></div>
                </div>
              </div>
              <div style="display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin-bottom:12px;">
                ${[
                  { key: 'reduced_meniscal_signal', label: 'Reduced meniscal signal' },
                  { key: 'meniscal_coverage_loss', label: 'Meniscal coverage loss' },
                  { key: 'structural_irregularity', label: 'Structural irregularity' },
                ].map(f => {
                  const detected = oa.findings[f.key as keyof typeof oa.findings];
                  return `<div style="
                    border-radius:5px;
                    border:1px solid ${detected ? '#fca5a5' : '#86efac'};
                    background:${detected ? '#fff5f5' : '#f0fdf4'};
                    color:${detected ? '#b91c1c' : '#15803d'};
                    font-size:11px; font-weight:600;
                    padding:6px 10px;
                    display:flex; align-items:center; gap:5px;
                  ">${detected ? '⚠ ' : '✓ '}${f.label}</div>`;
                }).join('')}
              </div>
              <div style="font-size:11px; color:#475569; border-top:1px solid ${isOA ? '#fca5a5' : '#86efac'}; padding-top:8px;">
                ${oa.notes}
              </div>
            </div>
            <div style="background:#fffbeb; border:1px solid #fde68a; border-left:3px solid #f59e0b; padding:8px 12px; border-radius:4px; font-size:10px; color:#92400e;">
              ${oa.clinical_warning}
            </div>
            ` : '<p style="font-size:12px; color:#64748b;">OA assessment not available for this scan.</p>'}
          </div>

          <!-- AI Analysis Result & Metrics -->
          <div class="section">
            <div class="section-title">AI Analysis & Segmentation Metrics</div>
            <div class="grid-4">
              <div class="metric-card">
                <div class="metric-label">Segmentation Confidence</div>
                <div class="metric-value">${hasProbabilityMean ? metrics!.probabilityMean!.toFixed(4) : 'N/A'}</div>
                <div class="metric-subtitle">Probability Mean</div>
              </div>
              <div class="metric-card">
                <div class="metric-label">Region Coverage</div>
                <div class="metric-value">${hasMaskFraction ? (metrics!.maskFraction! * 100).toFixed(2) + '%' : 'N/A'}</div>
                <div class="metric-subtitle">Mask Fraction</div>
              </div>
              <div class="metric-card">
                <div class="metric-label">Segmented Area</div>
                <div class="metric-value">${hasMaskArea ? metrics!.maskAreaPixels!.toLocaleString() : 'N/A'}</div>
                <div class="metric-subtitle">Mask Area (pixels)</div>
              </div>
              <div class="metric-card">
                <div class="metric-label">Inference Threshold</div>
                <div class="metric-value">${hasThreshold ? metrics!.threshold!.toFixed(2) : '0.50'}</div>
                <div class="metric-subtitle">Binarization Cutoff</div>
              </div>
            </div>
          </div>

          <!-- Medical Visual Results -->
          <div class="section">
            <div class="section-title">Medical Visual Results</div>
            <div class="grid-3">
              <div class="visual-box">
                <div class="visual-img-wrap">
                  ${originalImageSrc ? `<img src="${originalImageSrc}" alt="Original Knee Image" class="visual-img" />` : '<span style="color:#64748b;font-size:11px;">Image unavailable</span>'}
                </div>
                <div class="visual-caption">1. Original Knee X-Ray</div>
              </div>
              <div class="visual-box">
                <div class="visual-img-wrap">
                  ${maskImageSrc ? `<img src="${maskImageSrc}" alt="AI Segmentation Mask" class="visual-img" />` : '<span style="color:#64748b;font-size:11px;">Mask unavailable</span>'}
                </div>
                <div class="visual-caption">2. AI Segmentation Mask</div>
              </div>
              <div class="visual-box">
                <div class="visual-img-wrap">
                  ${overlayImageSrc ? `<img src="${overlayImageSrc}" alt="AI Overlay Visualization" class="visual-img" />` : '<span style="color:#64748b;font-size:11px;">Overlay unavailable</span>'}
                </div>
                <div class="visual-caption">3. AI Overlay Visualization</div>
              </div>
            </div>
          </div>

          <!-- AI-Assisted Result Summary -->
          <div class="section">
            <div class="section-title">AI-Assisted Result Summary</div>
            <div class="summary-box">
              The uploaded knee image was processed using the Nexora AI segmentation pipeline. The system successfully generated a segmentation mask and visual overlay for the analyzed image based on the U-Net deep learning architecture.
            </div>
          </div>

          <!-- Clinical Safety Disclaimer -->
          <div class="disclaimer-box">
            <div class="disclaimer-title">Clinical Safety Disclaimer</div>
            This report contains AI-assisted image analysis results generated by the Nexora system. It is intended to support clinical review and does not constitute a final medical diagnosis. Final interpretation and medical decisions must be made by a qualified healthcare professional.
          </div>

          <!-- Reviewer Sign-off -->
          <div class="signoff-section">
            <div>
              <div class="sig-line"></div>
              <div class="sig-label">Reviewing Clinician / Radiologist Signature</div>
            </div>
            <div>
              <div class="sig-line"></div>
              <div class="sig-label">Review Date & Clinical Notes</div>
            </div>
          </div>

          <div class="footer">
            Nexora AI Platform v0.1.0 • Report ID: ${reportId} • Confidential Medical Document
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
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <div>
              <DialogTitle className="text-xl font-bold flex items-center gap-2 text-primary">
                <FileText className="h-5 w-5" />
                Patient Medical Result Report
              </DialogTitle>
              <DialogDescription>
                Comprehensive AI analysis report ready for clinical review and printing.
              </DialogDescription>
            </div>
            <Badge variant="outline" className="bg-green-50 text-green-700 border-green-300 w-fit">
              <CheckCircle2 className="h-3.5 w-3.5 mr-1" />
              Analysis Completed
            </Badge>
          </div>
        </DialogHeader>

        {/* Report Preview Body */}
        <div className="space-y-6 py-4 bg-background">
          {/* Header Card */}
          <div className="rounded-lg border bg-muted/20 p-4 flex flex-col sm:flex-row justify-between gap-4">
            <div>
              <p className="text-xs uppercase font-bold text-primary tracking-wider">Nexora Medical AI</p>
              <h2 className="text-lg font-bold">PATIENT MEDICAL RESULT REPORT</h2>
              <p className="text-xs text-muted-foreground">Knee Medical Image Analysis</p>
            </div>
            <div className="text-left sm:text-right space-y-1 text-xs">
              <p><span className="text-muted-foreground">Report ID:</span> <span className="font-mono font-semibold">{reportId}</span></p>
              <p><span className="text-muted-foreground">Generated:</span> <span className="font-medium">{formattedDate}</span></p>
              <p><span className="text-muted-foreground">Scan Date:</span> <span className="font-medium">{scanDate}</span></p>
            </div>
          </div>

          {/* Patient Details */}
          <div>
            <h3 className="text-sm font-semibold mb-2 text-primary flex items-center gap-1.5">
              <Activity className="h-4 w-4" />
              Patient Information
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="rounded-md border p-2.5 bg-card">
                <p className="text-[11px] font-medium text-muted-foreground uppercase">Patient Name</p>
                <p className="text-sm font-semibold truncate">{patientNameDisplay}</p>
              </div>
              <div className="rounded-md border p-2.5 bg-card">
                <p className="text-[11px] font-medium text-muted-foreground uppercase">Patient ID</p>
                <p className="text-sm font-semibold truncate">{patientIdDisplay}</p>
              </div>
              <div className="rounded-md border p-2.5 bg-card">
                <p className="text-[11px] font-medium text-muted-foreground uppercase">Age</p>
                <p className="text-sm font-semibold">{ageDisplay}</p>
              </div>
              <div className="rounded-md border p-2.5 bg-card">
                <p className="text-[11px] font-medium text-muted-foreground uppercase">Sex / Gender</p>
                <p className="text-sm font-semibold">{sexDisplay}</p>
              </div>
            </div>
          </div>

          <Separator />

          {/* OA Assessment Verdict */}
          {oa && (
            <div className={`rounded-xl border-2 p-5 ${
              isOA
                ? 'border-red-300 bg-red-50 dark:border-red-800 dark:bg-red-950/40'
                : 'border-green-300 bg-green-50 dark:border-green-800 dark:bg-green-950/40'
            }`}>
              <div className="flex flex-wrap items-start justify-between gap-4 mb-3">
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground mb-1">
                    OA Assessment Result
                  </p>
                  <p className={`text-2xl font-extrabold tracking-tight ${
                    isOA ? 'text-red-700 dark:text-red-400' : 'text-green-700 dark:text-green-400'
                  }`}>
                    {isOA ? 'OA DETECTED' : 'NO OA FEATURES DETECTED'}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {isOA
                      ? 'This patient shows osteoarthritis features.'
                      : 'This patient shows no significant OA features.'}
                  </p>
                </div>
                <div className="flex flex-col items-end gap-1">
                  <Badge
                    variant="outline"
                    className={`text-sm px-3 py-1 font-bold ${
                      isOA
                        ? 'bg-red-100 text-red-800 border-red-300 dark:bg-red-900 dark:text-red-200'
                        : 'bg-green-100 text-green-800 border-green-300 dark:bg-green-900 dark:text-green-200'
                    }`}
                  >
                    {isOA ? 'OA Patient' : 'Non-OA Patient'}
                  </Badge>
                  {oa.severity !== 'None' && (
                    <Badge variant="outline" className="text-xs">Severity: {oa.severity}</Badge>
                  )}
                  <span className="text-xs text-muted-foreground">
                    Confidence: <strong>{oaConfidencePct}%</strong>
                  </span>
                </div>
              </div>

              {/* Confidence bar */}
              <div className="mb-3">
                <div className="h-2.5 rounded-full bg-muted overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${isOA ? 'bg-red-500' : 'bg-green-500'}`}
                    style={{ width: `${oaConfidencePct}%` }}
                  />
                </div>
              </div>

              {/* Findings chips */}
              <div className="flex flex-wrap gap-2 mb-3">
                {[
                  { key: 'reduced_meniscal_signal', label: 'Reduced meniscal signal' },
                  { key: 'meniscal_coverage_loss', label: 'Meniscal coverage loss' },
                  { key: 'structural_irregularity', label: 'Structural irregularity' },
                ].map(({ key, label }) => {
                  const detected = oa.findings[key as keyof typeof oa.findings];
                  return (
                    <span
                      key={key}
                      className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-xs font-medium ${
                        detected
                          ? 'border-red-200 bg-red-50/60 text-red-800 dark:border-red-700 dark:text-red-300'
                          : 'border-green-200 bg-green-50/60 text-green-800 dark:border-green-700 dark:text-green-300'
                      }`}
                    >
                      {detected ? '⚠' : '✓'} {label}
                    </span>
                  );
                })}
              </div>

              <p className="text-xs text-muted-foreground border-t pt-2">{oa.notes}</p>
            </div>
          )}

          {/* Real AI Segmentation Metrics */}
          <div>
            <h3 className="text-sm font-semibold mb-2 text-primary flex items-center gap-1.5">
              <Layers className="h-4 w-4" />
              Real AI Segmentation Metrics
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="rounded-md border border-primary/20 bg-primary/5 p-3 text-center">
                <p className="text-xs text-primary font-medium">Probability Mean</p>
                <p className="text-lg font-bold text-foreground">
                  {hasProbabilityMean ? metrics!.probabilityMean!.toFixed(4) : 'N/A'}
                </p>
                <p className="text-[10px] text-muted-foreground">Confidence Metric</p>
              </div>
              <div className="rounded-md border border-primary/20 bg-primary/5 p-3 text-center">
                <p className="text-xs text-primary font-medium">Mask Fraction</p>
                <p className="text-lg font-bold text-foreground">
                  {hasMaskFraction ? `${(metrics!.maskFraction! * 100).toFixed(2)}%` : 'N/A'}
                </p>
                <p className="text-[10px] text-muted-foreground">Region Coverage</p>
              </div>
              <div className="rounded-md border border-primary/20 bg-primary/5 p-3 text-center">
                <p className="text-xs text-primary font-medium">Mask Area</p>
                <p className="text-lg font-bold text-foreground">
                  {hasMaskArea ? metrics!.maskAreaPixels!.toLocaleString() : 'N/A'}
                </p>
                <p className="text-[10px] text-muted-foreground">Segmented Pixels</p>
              </div>
              <div className="rounded-md border border-primary/20 bg-primary/5 p-3 text-center">
                <p className="text-xs text-primary font-medium">Threshold</p>
                <p className="text-lg font-bold text-foreground">
                  {hasThreshold ? metrics!.threshold!.toFixed(2) : '0.50'}
                </p>
                <p className="text-[10px] text-muted-foreground">Inference Cutoff</p>
              </div>
            </div>
          </div>

          <Separator />

          {/* Visual Results (Original, Mask, Overlay) */}
          <div>
            <h3 className="text-sm font-semibold mb-3 text-primary flex items-center gap-1.5">
              <Sparkles className="h-4 w-4" />
              Medical Visual Results
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="border rounded-lg overflow-hidden bg-card text-center">
                <div className="h-44 bg-black flex items-center justify-center">
                  {originalImageSrc ? (
                    <img
                      src={originalImageSrc}
                      alt="Original Knee Scan"
                      className="max-h-44 max-w-full object-contain"
                    />
                  ) : (
                    <span className="text-xs text-muted-foreground">Image not available</span>
                  )}
                </div>
                <div className="p-2 border-t text-xs font-semibold">1. Original Knee Scan</div>
              </div>

              <div className="border rounded-lg overflow-hidden bg-card text-center">
                <div className="h-44 bg-black flex items-center justify-center">
                  {maskImageSrc ? (
                    <img
                      src={maskImageSrc}
                      alt="AI Segmentation Mask"
                      className="max-h-44 max-w-full object-contain"
                    />
                  ) : (
                    <span className="text-xs text-muted-foreground">Mask not available</span>
                  )}
                </div>
                <div className="p-2 border-t text-xs font-semibold">2. AI Segmentation Mask</div>
              </div>

              <div className="border rounded-lg overflow-hidden bg-card text-center">
                <div className="h-44 bg-black flex items-center justify-center">
                  {overlayImageSrc ? (
                    <img
                      src={overlayImageSrc}
                      alt="AI Overlay Visualization"
                      className="max-h-44 max-w-full object-contain"
                    />
                  ) : (
                    <span className="text-xs text-muted-foreground">Overlay not available</span>
                  )}
                </div>
                <div className="p-2 border-t text-xs font-semibold">3. AI Overlay Visualization</div>
              </div>
            </div>
          </div>

          {/* AI-Assisted Result Summary */}
          <div className="rounded-lg border bg-muted/30 p-3.5 space-y-1">
            <p className="text-xs font-semibold text-primary uppercase tracking-wide">AI-Assisted Result Summary</p>
            <p className="text-xs text-muted-foreground leading-relaxed">
              The uploaded knee image was processed using the Nexora AI segmentation pipeline. The system successfully generated a segmentation mask and visual overlay for the analyzed image.
            </p>
          </div>

          {/* Clinical Disclaimer */}
          <Alert className="border-amber-200 bg-amber-50 dark:bg-amber-950/40 dark:border-amber-900">
            <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400" />
            <AlertDescription className="text-xs text-amber-800 dark:text-amber-300">
              <strong>Clinical Safety Disclaimer:</strong> This report contains AI-assisted image analysis results generated by the Nexora system. It is intended to support clinical review and does not constitute a final medical diagnosis. Final interpretation and medical decisions must be made by a qualified healthcare professional.
            </AlertDescription>
          </Alert>
        </div>

        <DialogFooter className="border-t pt-4 flex-row justify-end gap-2">
          <Button variant="outline" onClick={onClose} disabled={printing}>
            Close
          </Button>
          <Button onClick={handlePrint} disabled={printing} className="gap-2">
            <Printer className="h-4 w-4" />
            {printing ? 'Preparing Print...' : 'Print Medical Report'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

