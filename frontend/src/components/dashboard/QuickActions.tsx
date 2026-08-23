import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Ruler, BarChart3, Users, History } from 'lucide-react';

export function QuickActions() {
  const navigate = useNavigate();

  const actions = [
    {
      title: 'Implant planning',
      description: 'Build patient-specific implant recommendations',
      icon: Ruler,
      onClick: () => navigate('/implant-sizing'),
      variant: 'default' as const,
    },
    {
      title: 'Progress view',
      description: 'Compare previous vs current AI scans for a patient',
      icon: History,
      onClick: () => navigate('/progress-view'),
      variant: 'outline' as const,
    },
    {
      title: 'OA dashboard',
      description: 'Monitor risk metrics and cohort trends',
      icon: BarChart3,
      onClick: () => navigate('/oa-analytics'),
      variant: 'outline' as const,
    },
    {
      title: 'Patient review',
      description: 'Open patient data and current imaging queue',
      icon: Users,
      onClick: () => navigate('/medical-imaging'),
      variant: 'outline' as const,
    },
  ];

  return (
    <Card className="glass-card border-0">
      <CardHeader>
        <CardTitle className="text-xl">Clinical workflow</CardTitle>
        <CardDescription>Distinct tools for diagnosis, review, and planning</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {actions.map(({ title, description, icon: Icon, onClick, variant }) => (
          <Button
            key={title}
            variant={variant}
            onClick={onClick}
            className="group h-auto justify-start rounded-2xl border border-slate-200 bg-gradient-to-br from-white to-slate-50 p-4 text-left shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md"
          >
            <div className="flex w-full items-start gap-3">
              <div className="rounded-xl bg-slate-900 p-2 text-white transition-colors group-hover:bg-primary">
                <Icon className="h-4 w-4" />
              </div>
              <div className="space-y-1">
                <div className="text-base font-semibold">{title}</div>
                <div className="text-sm text-slate-600">{description}</div>
              </div>
            </div>
          </Button>
        ))}
      </CardContent>
    </Card>
  );
}
