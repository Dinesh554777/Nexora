import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { Activity, Award } from 'lucide-react';
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
    <Card className="border-2 border-primary">
      <CardHeader className="bg-primary/5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Award className="h-5 w-5 text-primary" />
            <CardTitle>Recommended Implant</CardTitle>
          </div>
          <Badge variant="default" className="text-xs">Best Match</Badge>
        </div>
        <CardDescription>AI-generated sizing result</CardDescription>
      </CardHeader>
      <CardContent className="pt-6 space-y-6">
        <div>
          <h3 className="text-2xl font-bold mb-1">{recommendation.implantName}</h3>
          <p className="text-sm text-muted-foreground">{recommendation.implantId}</p>
        </div>

        <Separator />

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">Recommended Size</p>
            <p className="text-xl font-bold">{recommendation.size}</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">Rank</p>
            <p className="text-xl font-bold">#{recommendation.rank || 1}</p>
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-muted-foreground">Match Score</span>
            <span className="font-bold text-lg">{recommendation.matchScore}%</span>
          </div>
          <Progress value={recommendation.matchScore} className="h-2" />
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-muted-foreground">Confidence Level</span>
            <span className="font-bold text-lg">{recommendation.confidence}%</span>
          </div>
          <Progress value={recommendation.confidence} className="h-2" />
        </div>

        <div className="bg-muted/50 rounded-lg p-4">
          <p className="text-sm text-muted-foreground mb-1">Measurement Compatibility</p>
          <p className="text-lg font-semibold">{recommendation.measurementDifference.toFixed(2)} mm</p>
          <p className="text-xs text-muted-foreground mt-1">
            Euclidean distance between patient and implant measurements
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
