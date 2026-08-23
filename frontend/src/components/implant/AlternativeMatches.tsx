import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ImplantRecommendation } from '@/types';

interface AlternativeMatchesProps {
  alternatives: ImplantRecommendation[];
}

export function AlternativeMatches({ alternatives }: AlternativeMatchesProps) {
  if (alternatives.length === 0) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Alternative Options</CardTitle>
        <CardDescription>Additional compatible implants ranked by match score</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {alternatives.map((implant, index) => (
          <div key={implant.implantId} className="border-2 rounded-lg p-4 space-y-3 hover:border-primary/50 transition-colors">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <Badge variant="outline" className="text-xs">
                    #{implant.rank || index + 2}
                  </Badge>
                  <h4 className="font-semibold">{implant.implantName}</h4>
                </div>
                <p className="text-sm text-muted-foreground">{implant.implantId}</p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold">{implant.matchScore}%</p>
                <p className="text-xs text-muted-foreground">Match</p>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3 text-sm">
              <div>
                <p className="text-muted-foreground">Size</p>
                <p className="font-medium">{implant.size}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Confidence</p>
                <p className="font-medium">{implant.confidence}%</p>
              </div>
              <div>
                <p className="text-muted-foreground">Difference</p>
                <p className="font-medium">{implant.measurementDifference.toFixed(2)} mm</p>
              </div>
            </div>

            <div>
              <Progress value={implant.matchScore} className="h-1.5" />
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
