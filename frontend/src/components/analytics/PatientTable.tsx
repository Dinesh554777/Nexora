import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Patient } from '@/types';
import { Search } from 'lucide-react';

interface PatientTableProps {
  patients: Patient[];
}

export function PatientTable({ patients }: PatientTableProps) {
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<'all' | 'OA' | 'Non-OA'>('all');

  const filteredPatients = patients.filter(patient => {
    const matchesSearch = patient.id.toLowerCase().includes(search.toLowerCase());
    const matchesFilter = filter === 'all' || patient.oaStatus === filter;
    return matchesSearch && matchesFilter;
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Patient Data</CardTitle>
        <CardDescription>Detailed patient records and analysis results</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search by Patient ID..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>
          <div className="flex gap-2">
            <Badge
              variant={filter === 'all' ? 'default' : 'outline'}
              className="cursor-pointer"
              onClick={() => setFilter('all')}
            >
              All
            </Badge>
            <Badge
              variant={filter === 'OA' ? 'destructive' : 'outline'}
              className="cursor-pointer"
              onClick={() => setFilter('OA')}
            >
              OA
            </Badge>
            <Badge
              variant={filter === 'Non-OA' ? 'success' : 'outline'}
              className="cursor-pointer"
              onClick={() => setFilter('Non-OA')}
            >
              Non-OA
            </Badge>
          </div>
        </div>

        <div className="rounded-md border overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Patient ID</TableHead>
                <TableHead>Age</TableHead>
                <TableHead>Sex</TableHead>
                <TableHead>Meniscus Thickness (mm)</TableHead>
                <TableHead>OA Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredPatients.map((patient) => (
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
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        <p className="text-sm text-muted-foreground mt-4">
          Showing {filteredPatients.length} of {patients.length} patients
        </p>
      </CardContent>
    </Card>
  );
}
