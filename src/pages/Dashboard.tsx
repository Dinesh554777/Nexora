import { PageHeader } from '@/components/shared/PageHeader';
import { MetricCard } from '@/components/dashboard/MetricCard';
import { RecentAnalysis } from '@/components/dashboard/RecentAnalysis';
import { QuickActions } from '@/components/dashboard/QuickActions';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Users, AlertTriangle, UserCheck, Activity } from 'lucide-react';
import { demoPatients, calculateAnalytics } from '@/data/demoData';

export function Dashboard() {
  const analytics = calculateAnalytics(demoPatients);
  const implantRecommendations = 12; // Demo value

  return (
    <div className="space-y-8">
      <PageHeader
        title="Clinical Dashboard"
        description="AI-assisted orthopedic insights for knee assessment and implant planning"
      />

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Total Patients"
          value={analytics.totalPatients}
          description="Analyzed patients"
          icon={Users}
        />
        <MetricCard
          title="OA Patients"
          value={analytics.oaPatients}
          description={`${analytics.oaPercentage}% of total`}
          icon={AlertTriangle}
        />
        <MetricCard
          title="Non-OA Patients"
          value={analytics.nonOaPatients}
          description="Healthy assessments"
          icon={UserCheck}
        />
        <MetricCard
          title="Implant Recommendations"
          value={implantRecommendations}
          description="Generated this month"
          icon={Activity}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Osteoarthritis Overview</CardTitle>
            <CardDescription>Distribution of OA cases</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">OA Patients</span>
                  <span className="text-sm font-semibold">{analytics.oaPatients}</span>
                </div>
                <div className="h-3 rounded-full bg-muted overflow-hidden">
                  <div
                    className="h-full bg-destructive"
                    style={{ width: `${analytics.oaPercentage}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">Non-OA Patients</span>
                  <span className="text-sm font-semibold">{analytics.nonOaPatients}</span>
                </div>
                <div className="h-3 rounded-full bg-muted overflow-hidden">
                  <div
                    className="h-full bg-green-500"
                    style={{ width: `${100 - analytics.oaPercentage}%` }}
                  />
                </div>
              </div>

              <div className="pt-4 border-t">
                <p className="text-sm text-muted-foreground">
                  OA Prevalence: <span className="font-semibold">{analytics.oaPercentage}%</span>
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Meniscus Measurement</CardTitle>
            <CardDescription>Thickness distribution summary</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-sm text-muted-foreground mb-2">Average</p>
                <p className="text-2xl font-bold">{analytics.avgMeniscusThickness}</p>
                <p className="text-xs text-muted-foreground">mm</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-muted-foreground mb-2">Minimum</p>
                <p className="text-2xl font-bold">{analytics.minMeniscusThickness}</p>
                <p className="text-xs text-muted-foreground">mm</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-muted-foreground mb-2">Maximum</p>
                <p className="text-2xl font-bold">{analytics.maxMeniscusThickness}</p>
                <p className="text-xs text-muted-foreground">mm</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <RecentAnalysis patients={demoPatients} />

      <QuickActions />
    </div>
  );
}
