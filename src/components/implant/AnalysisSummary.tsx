import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { CheckCircle, Clock } from 'lucide-react';
import { ImplantRecommendation } from '@/types';

interface AnalysisSummaryProps {
  recommendation: ImplantRecommendation;
}

export function AnalysisSummary({ recommendation }: AnalysisSummaryProps) {
  const currentTime = new Date().toLocaleString();

  return (
    <Card className="border-primary/20 bg-primary/5">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-green-600" />
            AI Analysis Summary
          </CardTitle>
          <Badge variant="outline" className="gap-1">
            <Clock className="h-3 w-3" />
            {currentTime}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-muted-foreground mb-1">Analysis Status</p>
            <div className="flex items-center gap-2">
              <Badge variant="default" className="bg-green-600">Complete</Badge>
            </div>
          </div>
          <div>
            <p className="text-sm text-muted-foreground mb-1">Input Measurements</p>
            <p className="font-medium">4 dimensions analyzed</p>
          </div>
        </div>

        <Separator />

        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-muted-foreground mb-1">Recommended Implant</p>
            <p className="font-semibold">{recommendation.implantName}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground mb-1">Recommended Size</p>
            <p className="font-semibold">{recommendation.size}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-muted-foreground mb-1">Match Score</p>
            <p className="text-xl font-bold text-primary">{recommendation.matchScore}%</p>
          </div>
          {recommendation.confidence !== undefined && (
            <div>
              <p className="text-sm text-muted-foreground mb-1">Model Confidence</p>
              <p className="text-xl font-bold text-primary">{recommendation.confidence}%</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
