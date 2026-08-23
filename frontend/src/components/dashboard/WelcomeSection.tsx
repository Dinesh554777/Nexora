import { useNavigate } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Activity, BarChart3, ArrowRight } from 'lucide-react';

export function WelcomeSection() {
  const navigate = useNavigate();

  const highlights = [
    'OA risk scoring',
    'Image triage',
    'Implant matching',
    'Clinical review'
  ];

  return (
    <Card className="glass-card overflow-hidden border-0 bg-gradient-to-br from-primary/8 via-white to-cyan-50">
      <CardContent className="p-6 md:p-8">
        <div className="flex flex-col gap-8 xl:flex-row xl:items-center xl:justify-between">
          <div className="flex-1 space-y-5">
            <div className="feature-badge">Proactive orthopedic intelligence</div>

            <div className="flex items-center gap-3">
              <div className="rounded-2xl bg-gradient-to-br from-primary to-cyan-500 p-3 shadow-lg shadow-primary/20">
                <Activity className="h-7 w-7 text-white" />
              </div>
              <div>
                <h2 className="text-3xl font-bold tracking-tight md:text-4xl">KneeVision AI</h2>
                <p className="text-sm text-muted-foreground md:text-base">
                  AI-powered orthopedic analysis platform
                </p>
              </div>
            </div>

            <p className="max-w-2xl text-base text-slate-700 md:text-lg">
              Detect osteoarthritis patterns, review imaging studies, and match implant solutions with a single clinical workflow designed for faster decisions.
            </p>

            <div className="flex flex-wrap gap-2">
              {highlights.map((item) => (
                <span
                  key={item}
                  className="rounded-full border border-slate-200 bg-white/80 px-3 py-1.5 text-xs font-medium text-slate-700"
                >
                  {item}
                </span>
              ))}
            </div>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row xl:flex-col">
            <Button
              size="lg"
              onClick={() => navigate('/implant-sizing')}
              className="gap-2 rounded-xl px-5 shadow-lg shadow-primary/20"
            >
              Start Implant Analysis
              <ArrowRight className="h-4 w-4" />
            </Button>
            <Button
              size="lg"
              variant="outline"
              onClick={() => navigate('/oa-analytics')}
              className="gap-2 rounded-xl border-slate-200 bg-white/90"
            >
              <BarChart3 className="h-4 w-4" />
              View OA Analytics
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
