import { PageHeader } from '@/components/shared/PageHeader';
import { MetricCard } from '@/components/dashboard/MetricCard';
import { PatientTable } from '@/components/analytics/PatientTable';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Users, AlertTriangle, UserCheck, Percent } from 'lucide-react';
import { demoPatients, calculateAnalytics } from '@/data/demoData';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, ScatterChart, Scatter } from 'recharts';

export function OAAnalytics() {
  const analytics = calculateAnalytics(demoPatients);

  // Prepare chart data
  const oaData = [
    { name: 'OA', value: analytics.oaPatients, fill: '#ef4444' },
    { name: 'Non-OA', value: analytics.nonOaPatients, fill: '#22c55e' },
  ];

  const ageGroups = [
    { age: '30-40', OA: 0, NonOA: 3 },
    { age: '41-50', OA: 0, NonOA: 4 },
    { age: '51-60', OA: 1, NonOA: 0 },
    { age: '61-70', OA: 4, NonOA: 0 },
    { age: '71-80', OA: 3, NonOA: 0 },
  ];

  const sexData = [
    { sex: 'Male', OA: 5, NonOA: 2 },
    { sex: 'Female', OA: 3, NonOA: 5 },
  ];

  const scatterData = demoPatients.map(p => ({
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
              <BarChart data={ageGroups}>
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
              <BarChart data={sexData}>
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

      <PatientTable patients={demoPatients} />
    </div>
  );
}
