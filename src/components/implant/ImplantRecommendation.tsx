import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { Activity } from 'lucide-react';
import { ImplantRecommendation as ImplantRec } from '@/types';

interface ImplantRecommendationProps {
  recommendation: ImplantRec | null;
}

export function ImplantRecommendation({ recommendation }: ImplantRecommendationProps) {
  if (!recommendation) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Implant Recommendation</CardTitle>
          <CardDescription>No analysis performed</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center py-12 text-center">
          <div className="rounded-full bg-muted p-6 mb-4">
            <Activity className="h-12 w-12 text-muted-foreground" />
          </div>
          <h3 className="font-semibold text-lg mb-2">Ready to Analyze</h3>
          <p className="text-sm text-muted-foreground max-w-sm">
            Enter patient measurements to generate an AI-powered implant recommendation
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Implant Recommendation</CardTitle>
        <CardDescription>AI-generated sizing result</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-muted-foreground">Recommended Implant</span>
            <Badge variant="default">Best Match</Badge>
          </div>
          <h3 className="text-2xl font-bold">{recommendation.implantName}</h3>
        </div>

        <Separator />

        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-muted-foreground mb-1">Implant ID</p>
            <p className="font-semibold">{recommendation.implantId}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground mb-1">Size</p>
            <p className="font-semibold">{recommendation.size}</p>
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">Match Score</span>
            <span className="font-semibold">{recommendation.matchScore}%</span>
          </div>
          <Progress value={recommendation.matchScore} />
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">Confidence</span>
            <span className="font-semibold">{recommendation.confidence}%</span>
          </div>
          <Progress value={recommendation.confidence} />
        </div>

        <div className="bg-muted/50 rounded-lg p-4">
          <p className="text-sm text-muted-foreground mb-1">Measurement Difference</p>
          <p className="text-lg font-semibold">{recommendation.measurementDifference.toFixed(2)} mm</p>
        </div>
      </CardContent>
    </Card>
  );
}
