import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { HelpCircle, CheckCircle2, TrendingDown } from 'lucide-react';
import { ImplantRecommendation } from '@/types';

interface WhyThisImplantProps {
  recommendation: ImplantRecommendation;
}

export function WhyThisImplant({ recommendation }: WhyThisImplantProps) {
  const hasExplainabilityData = 
    recommendation.matchScore !== undefined &&
    recommendation.measurementDifference !== undefined;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <HelpCircle className="h-5 w-5 text-primary" />
          <CardTitle>Why This Implant?</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {hasExplainabilityData ? (
          <>
            <div className="flex items-start gap-3 p-3 rounded-lg bg-muted/50">
              <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-medium mb-1">High Match Score</p>
                <p className="text-sm text-muted-foreground">
                  This implant achieved a match score of <strong>{recommendation.matchScore}%</strong> based 
                  on the comparison of patient measurements with implant dimensions.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3 p-3 rounded-lg bg-muted/50">
              <TrendingDown className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-medium mb-1">Measurement Compatibility</p>
                <p className="text-sm text-muted-foreground">
                  The Euclidean distance between patient and implant measurements 
                  is <strong>{recommendation.measurementDifference.toFixed(2)} mm</strong>, indicating 
                  close dimensional compatibility.
                </p>
              </div>
            </div>

            {recommendation.rank && (
              <div className="flex items-start gap-3 p-3 rounded-lg bg-muted/50">
                <Badge className="mt-0.5">#{recommendation.rank}</Badge>
                <div>
                  <p className="font-medium mb-1">Top Ranked Option</p>
                  <p className="text-sm text-muted-foreground">
                    This implant was ranked highest among all available options 
                    in the database.
                  </p>
                </div>
              </div>
            )}

            {recommendation.confidence !== undefined && (
              <div className="p-3 rounded-lg bg-primary/5 border border-primary/20">
                <p className="text-sm">
                  <strong>Model Confidence:</strong> The AI model has {recommendation.confidence}% 
                  confidence in this recommendation based on the measurement analysis.
                </p>
              </div>
            )}
          </>
        ) : (
          <div className="p-4 rounded-lg bg-muted/50 text-center">
            <p className="text-sm text-muted-foreground">
              Recommendation is based on the measurement matching model.
            </p>
          </div>
        )}

        <div className="pt-2 border-t text-xs text-muted-foreground">
          <p>
            This analysis uses Euclidean distance calculation to compare patient knee 
            measurements with pre-defined implant dimensions.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
