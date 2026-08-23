import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Database } from 'lucide-react';
import { AnalyticsResponse } from '@/types/api';

interface DatasetOverviewProps {
  analytics: AnalyticsResponse;
}

export function DatasetOverview({ analytics }: DatasetOverviewProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Database className="h-5 w-5 text-primary" />
          <CardTitle>Dataset Overview</CardTitle>
        </div>
        <CardDescription>Summary of analyzed patient population</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-4 rounded-lg bg-muted/50">
            <p className="text-3xl font-bold text-primary">{analytics.totalPatients}</p>
            <p className="text-sm text-muted-foreground mt-1">Total Patients</p>
          </div>
          <div className="text-center p-4 rounded-lg bg-destructive/10">
            <p className="text-3xl font-bold text-destructive">{analytics.oaPatients}</p>
            <p className="text-sm text-muted-foreground mt-1">OA Patients</p>
          </div>
          <div className="text-center p-4 rounded-lg bg-green-500/10">
            <p className="text-3xl font-bold text-green-600">{analytics.nonOaPatients}</p>
            <p className="text-sm text-muted-foreground mt-1">Non-OA Patients</p>
          </div>
          <div className="text-center p-4 rounded-lg bg-primary/10">
            <p className="text-3xl font-bold text-primary">{analytics.oaPercentage}%</p>
            <p className="text-sm text-muted-foreground mt-1">OA Prevalence</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
