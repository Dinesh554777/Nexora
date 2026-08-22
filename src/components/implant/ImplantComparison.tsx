import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { ImplantRecommendation } from '@/types';

interface ImplantComparisonProps {
  recommendation: ImplantRecommendation;
  alternatives: ImplantRecommendation[];
}

export function ImplantComparison({ recommendation, alternatives }: ImplantComparisonProps) {
  const allImplants = [recommendation, ...alternatives];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Compare Implant Options</CardTitle>
        <CardDescription>Side-by-side comparison of all analyzed implants</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[80px]">Rank</TableHead>
                <TableHead>Implant Name</TableHead>
                <TableHead>Size</TableHead>
                <TableHead className="text-right">Match Score</TableHead>
                <TableHead className="text-right">Difference</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {allImplants.map((implant, index) => {
                const isRecommended = index === 0;
                return (
                  <TableRow key={implant.implantId} className={isRecommended ? 'bg-primary/5' : ''}>
                    <TableCell>
                      <Badge variant={isRecommended ? 'default' : 'outline'}>
                        #{implant.rank || index + 1}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-medium">
                      <div>
                        <p>{implant.implantName}</p>
                        <p className="text-xs text-muted-foreground">{implant.implantId}</p>
                      </div>
                    </TableCell>
                    <TableCell>{implant.size}</TableCell>
                    <TableCell className="text-right">
                      <span className="font-semibold">{implant.matchScore}%</span>
                    </TableCell>
                    <TableCell className="text-right">
                      {implant.measurementDifference.toFixed(2)} mm
                    </TableCell>
                    <TableCell>
                      {isRecommended ? (
                        <Badge variant="default">Recommended</Badge>
                      ) : (
                        <Badge variant="secondary">Alternative</Badge>
                      )}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}
