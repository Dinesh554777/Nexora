import { useEffect, useState } from 'react';
import { PageHeader } from '@/components/shared/PageHeader';
import { MetricCard } from '@/components/dashboard/MetricCard';
import { RecentAnalysis } from '@/components/dashboard/RecentAnalysis';
import { QuickActions } from '@/components/dashboard/QuickActions';
import { WelcomeSection } from '@/components/dashboard/WelcomeSection';
import { ClinicalWorkflow } from '@/components/dashboard/ClinicalWorkflow';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { ErrorRetry } from '@/components/shared/ErrorRetry';
import { Users, AlertTriangle, UserCheck, Activity } from 'lucide-react';
import { apiService } from '@/services/api';
import { Patient } from '@/types';
import { AnalyticsResponse } from '@/types/api';

export function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiService.getAnalytics();
      setAnalytics(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load dashboard data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="space-y-8">
        <PageHeader
          title="Clinical Dashboard"
          description="Loading clinical insights..."
        />
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <Skeleton className="h-24 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error || !analytics) {
    return (
      <div className="space-y-8">
        <PageHeader
          title="Clinical Dashboard"
          description="AI-assisted orthopedic insights for knee assessment and implant planning"
        />
        <ErrorRetry
          title="Error Loading Dashboard"
          message={error || 'Unable to load dashboard data. Please check your connection and try again.'}
          onRetry={fetchAnalytics}
        />
      </div>
    );
  }

  // Convert API patients to frontend type
  const patients: Patient[] = analytics.patients.map(p => ({
    id: p.id,
    age: p.age,
    sex: p.sex,
    meniscusThickness: p.meniscusThickness,
    oaStatus: p.oaStatus,
    analysisStatus: p.analysisStatus,
  }));

  const implantRecommendations = 12; // Demo value for now

  return (
    <div className="space-y-8">
      <PageHeader
        title="Clinical Dashboard"
        description="AI-assisted orthopedic insights for knee assessment and implant planning"
      />

      <WelcomeSection />

      <ClinicalWorkflow />

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

      <RecentAnalysis patients={patients} />

      <QuickActions />
    </div>
  );
}
