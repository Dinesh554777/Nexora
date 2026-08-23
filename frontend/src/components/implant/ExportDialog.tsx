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
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Download, FileJson, Printer, CheckCircle2 } from 'lucide-react';
import { ExportData } from '@/types';

interface ExportDialogProps {
  isOpen: boolean;
  onClose: () => void;
  exportData: ExportData;
}

export function ExportDialog({ isOpen, onClose, exportData }: ExportDialogProps) {
  const [exportFormat, setExportFormat] = useState<'json' | 'print'>('json');
  const [exporting, setExporting] = useState(false);
  const [exportSuccess, setExportSuccess] = useState(false);

  const handleExport = () => {
    setExporting(true);

    if (exportFormat === 'json') {
      // Export as JSON
      const jsonData = JSON.stringify(exportData, null, 2);
      const blob = new Blob([jsonData], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `kneevision-analysis-${Date.now()}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      setTimeout(() => {
        setExporting(false);
        setExportSuccess(true);
        setTimeout(() => {
          setExportSuccess(false);
          onClose();
        }, 2000);
      }, 1000);
    } else {
      // Open print dialog with formatted report
      const printWindow = window.open('', '_blank');
      if (printWindow) {
        printWindow.document.write(generatePrintableReport(exportData));
        printWindow.document.close();
        setTimeout(() => {
          printWindow.print();
          setExporting(false);
          onClose();
        }, 500);
      } else {
        setExporting(false);
        alert('Please allow popups to print the report.');
      }
    }
  };

  const generatePrintableReport = (data: ExportData): string => {
    return `
      <!DOCTYPE html>
      <html>
      <head>
        <title>KneeVision AI Analysis Report</title>
        <style>
          body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            color: #333;
          }
          h1 {
            color: #1e40af;
            border-bottom: 3px solid #1e40af;
            padding-bottom: 10px;
          }
          h2 {
            color: #4f46e5;
            margin-top: 30px;
            border-bottom: 1px solid #e5e7eb;
            padding-bottom: 5px;
          }
          .section {
            margin: 20px 0;
          }
          .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin: 15px 0;
          }
          .field {
            padding: 10px;
            background: #f9fafb;
            border-radius: 5px;
          }
          .label {
            font-weight: bold;
            color: #6b7280;
            font-size: 12px;
            text-transform: uppercase;
          }
          .value {
            font-size: 18px;
            color: #111827;
            margin-top: 5px;
          }
          table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
          }
          th, td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #e5e7eb;
          }
          th {
            background: #f3f4f6;
            font-weight: bold;
          }
          .disclaimer {
            margin-top: 40px;
            padding: 15px;
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            font-size: 12px;
          }
          .footer {
            margin-top: 40px;
            text-align: center;
            color: #6b7280;
            font-size: 12px;
          }
          @media print {
            body {
              margin: 0;
              padding: 20px;
            }
          }
        </style>
      </head>
      <body>
        <h1>KneeVision AI Analysis Report</h1>
        <div class="section">
          <p><strong>Generated:</strong> ${new Date(data.timestamp).toLocaleString()}</p>
        </div>

        ${data.patientInfo ? `
        <h2>Patient Information</h2>
        <div class="grid">
          ${data.patientInfo.patientId ? `
          <div class="field">
            <div class="label">Patient ID</div>
            <div class="value">${data.patientInfo.patientId}</div>
          </div>
          ` : ''}
          ${data.patientInfo.age ? `
          <div class="field">
            <div class="label">Age</div>
            <div class="value">${data.patientInfo.age}</div>
          </div>
          ` : ''}
          ${data.patientInfo.sex ? `
          <div class="field">
            <div class="label">Sex</div>
            <div class="value">${data.patientInfo.sex}</div>
          </div>
          ` : ''}
        </div>
        ` : ''}

        ${data.measurements ? `
        <h2>Knee Measurements</h2>
        <div class="grid">
          <div class="field">
            <div class="label">Femur Width</div>
            <div class="value">${data.measurements.femurWidth.toFixed(1)} mm</div>
          </div>
          <div class="field">
            <div class="label">Femur AP</div>
            <div class="value">${data.measurements.femurAP.toFixed(1)} mm</div>
          </div>
          <div class="field">
            <div class="label">Tibia Width</div>
            <div class="value">${data.measurements.tibiaWidth.toFixed(1)} mm</div>
          </div>
          <div class="field">
            <div class="label">Tibia AP</div>
            <div class="value">${data.measurements.tibiaAP.toFixed(1)} mm</div>
          </div>
        </div>
        ` : ''}

        ${data.recommendation ? `
        <h2>Implant Recommendation</h2>
        <div class="section">
          <table>
            <tr>
              <th>Implant</th>
              <th>Size</th>
              <th>Match Score</th>
              <th>Confidence</th>
              <th>Difference</th>
            </tr>
            <tr>
              <td><strong>${data.recommendation.implantName}</strong></td>
              <td>${data.recommendation.size}</td>
              <td>${data.recommendation.matchScore}%</td>
              <td>${data.recommendation.confidence}%</td>
              <td>${data.recommendation.measurementDifference.toFixed(2)} mm</td>
            </tr>
          </table>
        </div>
        ` : ''}

        ${data.alternatives && data.alternatives.length > 0 ? `
        <h2>Alternative Options</h2>
        <div class="section">
          <table>
            <tr>
              <th>Rank</th>
              <th>Implant</th>
              <th>Size</th>
              <th>Match Score</th>
              <th>Difference</th>
            </tr>
            ${data.alternatives.map(alt => `
            <tr>
              <td>${alt.rank || '-'}</td>
              <td>${alt.implantName}</td>
              <td>${alt.size}</td>
              <td>${alt.matchScore}%</td>
              <td>${alt.measurementDifference.toFixed(2)} mm</td>
            </tr>
            `).join('')}
          </table>
        </div>
        ` : ''}

        ${data.imageAnalysis && data.imageAnalysis.length > 0 ? `
        <h2>Medical Image Analysis</h2>
        ${data.imageAnalysis.map((analysis, idx) => `
        <div class="section">
          <h3>Image ${idx + 1} - Confidence: ${analysis.confidence}%</h3>
          <p><strong>Findings:</strong></p>
          <ul>
            ${analysis.findings.map(f => `<li>${f}</li>`).join('')}
          </ul>
          ${analysis.oaAssessment ? `
          <p><strong>OA Assessment:</strong> ${analysis.oaAssessment.classification} (${analysis.oaAssessment.severity})</p>
          ` : ''}
        </div>
        `).join('')}
        ` : ''}

        <div class="disclaimer">
          <strong>Medical Disclaimer:</strong> AI-generated recommendations are intended to support clinical 
          decision-making. Final implant selection and medical decisions must be reviewed by a qualified 
          healthcare professional considering patient history, surgical planning, and clinical judgment.
        </div>

        <div class="footer">
          <p>KneeVision AI - AI-Powered Orthopedic Analysis</p>
          <p>Report generated on ${new Date(data.timestamp).toLocaleString()}</p>
        </div>
      </body>
      </html>
    `;
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Export Analysis Report</DialogTitle>
          <DialogDescription>
            Choose a format to export your analysis results
          </DialogDescription>
        </DialogHeader>

        {exportSuccess ? (
          <div className="py-8">
            <div className="flex flex-col items-center gap-3">
              <div className="h-12 w-12 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center">
                <CheckCircle2 className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <p className="text-lg font-semibold">Export Successful!</p>
              <p className="text-sm text-muted-foreground text-center">
                Your analysis report has been exported successfully.
              </p>
            </div>
          </div>
        ) : (
          <>
            <div className="space-y-6 py-4">
              <RadioGroup value={exportFormat} onValueChange={(value: string) => setExportFormat(value as 'json' | 'print')}>
                <div className="flex items-start space-x-3 p-4 border rounded-lg cursor-pointer hover:bg-muted/50 transition-colors">
                  <RadioGroupItem value="json" id="json" />
                  <div className="flex-1">
                    <Label htmlFor="json" className="cursor-pointer flex items-center gap-2 font-semibold">
                      <FileJson className="h-5 w-5 text-primary" />
                      Export as JSON
                    </Label>
                    <p className="text-sm text-muted-foreground mt-1">
                      Download a machine-readable JSON file with complete analysis data
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-3 p-4 border rounded-lg cursor-pointer hover:bg-muted/50 transition-colors">
                  <RadioGroupItem value="print" id="print" />
                  <div className="flex-1">
                    <Label htmlFor="print" className="cursor-pointer flex items-center gap-2 font-semibold">
                      <Printer className="h-5 w-5 text-primary" />
                      Print Report
                    </Label>
                    <p className="text-sm text-muted-foreground mt-1">
                      Open a printable PDF-ready report for printing or saving
                    </p>
                  </div>
                </div>
              </RadioGroup>

              <Separator />

              <Alert>
                <AlertDescription className="text-sm">
                  <strong>Note:</strong> Exported reports contain comprehensive analysis data including measurements,
                  recommendations, and confidence metrics. Ensure compliance with data protection regulations.
                </AlertDescription>
              </Alert>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={onClose} disabled={exporting}>
                Cancel
              </Button>
              <Button onClick={handleExport} disabled={exporting} className="gap-2">
                {exporting ? (
                  <>Processing...</>
                ) : (
                  <>
                    <Download className="h-4 w-4" />
                    Export
                  </>
                )}
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
