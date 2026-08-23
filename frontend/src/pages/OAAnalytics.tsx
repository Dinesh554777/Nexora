import { useEffect, useState } from 'react';
import { PageHeader } from '@/components/shared/PageHeader';
import { MetricCard } from '@/components/dashboard/MetricCard';
import { PatientTable } from '@/components/analytics/PatientTable';
import { DatasetOverview } from '@/components/analytics/DatasetOverview';
import { ClinicalObservations } from '@/components/analytics/ClinicalObservations';
import { AnalyticsFilters, FilterState } from '@/components/analytics/AnalyticsFilters';
import { ClinicalDisclaimer } from '@/components/shared/ClinicalDisclaimer';
import { ErrorRetry } from '@/components/shared/ErrorRetry';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Users, AlertTriangle, UserCheck, Percent } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, ScatterChart, Scatter } from 'recharts';
import { apiService } from '@/services/api';
import { Patient } from '@/types';
import { AnalyticsResponse } from '@/types/api';
import { filterPatientsByOAStatus } from '@/lib/analytics';

export function OAAnalytics() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null);
  const [filters, setFilters] = useState<FilterState>({ oaStatus: 'All' });

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiService.getAnalytics();
      setAnalytics(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load analytics data';
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
          title="OA Analytics"
          description="Loading clinical analytics..."
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
          title="OA Analytics"
          description="Explore osteoarthritis patterns across the analyzed knee dataset"
        />
        <ErrorRetry
          title="Error Loading Analytics"
          message={error || 'Unable to load analytics data. Please check your connection and try again.'}
          onRetry={fetchAnalytics}
        />
      </div>
    );
  }

  // Convert API patients to frontend type
  const allPatients: Patient[] = analytics.patients.map(p => ({
    id: p.id,
    age: p.age,
    sex: p.sex,
    meniscusThickness: p.meniscusThickness,
    oaStatus: p.oaStatus,
    analysisStatus: p.analysisStatus,
  }));

  // Apply filters
  const patients = filterPatientsByOAStatus(allPatients, filters.oaStatus);

  // Prepare chart data
  const oaData = [
    { name: 'OA', value: analytics.oaPatients, fill: '#ef4444' },
    { name: 'Non-OA', value: analytics.nonOaPatients, fill: '#22c55e' },
  ];

  const scatterData = patients.map(p => ({
    age: p.age,
    thickness: p.meniscusThickness,
    oa: p.oaStatus,
  }));

  return (
    <div className="space-y-8">
      <PageHeader
        title="OA Analytics"
        description="Explore osteoarthritis patterns across the analyzed knee dataset"
      />

      {/* Dataset Overview & Observations */}
      <div className="grid gap-6 lg:grid-cols-2">
        <DatasetOverview analytics={analytics} />
        <ClinicalObservations analytics={analytics} />
      </div>

      {/* Filters */}
      <AnalyticsFilters filters={filters} onFilterChange={setFilters} />

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Total Patients"
          value={analytics.totalPatients}
          icon={Users}
        />
        <MetricCard
          title="OA Patients"
          value={analytics.oaPatients}
          icon={AlertTriangle}
        />
        <MetricCard
          title="Non-OA Patients"
          value={analytics.nonOaPatients}
          icon={UserCheck}
        />
        <MetricCard
          title="OA Percentage"
          value={`${analytics.oaPercentage}%`}
          icon={Percent}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>OA vs Non-OA Distribution</CardTitle>
            <CardDescription>Patient classification breakdown</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={oaData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry.name}: ${entry.value}`}
                  outerRadius={100}
                  dataKey="value"
                >
                  {oaData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Age Distribution</CardTitle>
            <CardDescription>OA prevalence by age group</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={analytics.ageDistribution}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="age" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="OA" fill="#ef4444" />
                <Bar dataKey="NonOA" fill="#22c55e" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Sex Distribution</CardTitle>
            <CardDescription>OA patterns by biological sex</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={analytics.sexDistribution}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="sex" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="OA" fill="#ef4444" />
                <Bar dataKey="NonOA" fill="#22c55e" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Age vs Meniscus Thickness</CardTitle>
            <CardDescription>Correlation analysis</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <ScatterChart>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="age" name="Age" unit=" yrs" />
                <YAxis dataKey="thickness" name="Thickness" unit=" mm" />
                <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                <Legend />
                <Scatter
                  name="OA"
                  data={scatterData.filter(d => d.oa === 'OA')}
                  fill="#ef4444"
                />
                <Scatter
                  name="Non-OA"
                  data={scatterData.filter(d => d.oa === 'Non-OA')}
                  fill="#22c55e"
                />
              </ScatterChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <PatientTable patients={patients} />

      <ClinicalDisclaimer />
    </div>
  );
}
