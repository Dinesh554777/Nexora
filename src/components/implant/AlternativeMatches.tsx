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
        <CardTitle>Alternative Matches</CardTitle>
        <CardDescription>Additional compatible implants</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {alternatives.map((implant, index) => (
          <div key={implant.implantId} className="border rounded-lg p-4 space-y-3">
            <div className="flex items-start justify-between">
              <div>
                <h4 className="font-semibold">{implant.implantName}</h4>
                <p className="text-sm text-muted-foreground">{implant.implantId}</p>
              </div>
              <Badge variant="outline">Rank #{implant.rank || index + 2}</Badge>
            </div>

            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <p className="text-muted-foreground">Size</p>
                <p className="font-medium">{implant.size}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Difference</p>
                <p className="font-medium">{implant.measurementDifference.toFixed(2)} mm</p>
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-muted-foreground">Match Score</span>
                <span className="text-sm font-semibold">{implant.matchScore}%</span>
              </div>
              <Progress value={implant.matchScore} />
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
