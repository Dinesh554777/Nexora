import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Progress } from '@/components/ui/progress';
import { AlertTriangle, CheckCircle2, Eye, Activity } from 'lucide-react';
import { ImageAnalysisResult } from '@/types';

interface AnalysisResultsProps {
  results: ImageAnalysisResult[];
}

export function AnalysisResults({ results }: AnalysisResultsProps) {
  if (results.length === 0) {
    return null;
  }

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

  return (
    <div className="space-y-6">
      {/* Medical Disclaimer */}
      <Alert className="border-orange-200 bg-orange-50 dark:bg-orange-950 dark:border-orange-900">
        <AlertTriangle className="h-5 w-5 text-orange-600 dark:text-orange-400" />
        <AlertTitle className="text-orange-800 dark:text-orange-200">
          AI-Assisted Analysis
        </AlertTitle>
        <AlertDescription className="text-orange-700 dark:text-orange-300">
          AI-assisted analysis is intended to support clinical decision-making and does not replace 
          professional medical diagnosis. All findings require review and confirmation by a qualified healthcare professional.
        </AlertDescription>
      </Alert>

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
            {/* Key Findings */}
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

            {/* Abnormal Regions */}
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

            {/* Measurements */}
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

            {/* OA Indicators */}
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

            {/* Clinical Review Note */}
            <Alert className="bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-900">
              <AlertDescription className="text-sm text-blue-800 dark:text-blue-200">
                <strong>Note:</strong> These findings require clinical review and confirmation. 
                Consult with a qualified healthcare professional for diagnosis and treatment planning.
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
