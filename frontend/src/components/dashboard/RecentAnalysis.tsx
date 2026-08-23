import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Patient } from '@/types';

interface RecentAnalysisProps {
  patients: Patient[];
}

export function RecentAnalysis({ patients }: RecentAnalysisProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Analysis</CardTitle>
        <CardDescription>Latest patient assessments</CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Patient ID</TableHead>
              <TableHead>Age</TableHead>
              <TableHead>Sex</TableHead>
              <TableHead>Meniscus (mm)</TableHead>
              <TableHead>OA Status</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {patients.slice(0, 5).map((patient) => (
              <TableRow key={patient.id}>
                <TableCell className="font-medium">{patient.id}</TableCell>
                <TableCell>{patient.age}</TableCell>
                <TableCell>{patient.sex}</TableCell>
                <TableCell>{patient.meniscusThickness.toFixed(1)}</TableCell>
                <TableCell>
                  <Badge variant={patient.oaStatus === 'OA' ? 'destructive' : 'success'}>
                    {patient.oaStatus}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Badge variant="secondary">{patient.analysisStatus}</Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
