import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle2, Ruler, Brain, Award } from 'lucide-react';
import { cn } from '@/lib/utils';

export function AnalysisTimeline() {
  const steps = [
    {
      icon: Ruler,
      title: 'Patient Measurements',
      description: 'Knee dimensions captured',
      completed: true,
    },
    {
      icon: Brain,
      title: 'Measurement Analysis',
      description: 'Euclidean distance calculated',
      completed: true,
    },
    {
      icon: CheckCircle2,
      title: 'Implant Matching',
      description: 'Database comparison performed',
      completed: true,
    },
    {
      icon: Award,
      title: 'Recommendation',
      description: 'Best match identified',
      completed: true,
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Analysis Process</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {steps.map((step, index) => {
            const Icon = step.icon;
            return (
              <div key={index} className="relative flex items-start gap-4">
                {index < steps.length - 1 && (
                  <div className="absolute left-5 top-12 bottom-0 w-0.5 bg-primary/20" />
                )}
                <div
                  className={cn(
                    "flex items-center justify-center w-10 h-10 rounded-full flex-shrink-0 z-10",
                    step.completed
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground"
                  )}
                >
                  <Icon className="h-5 w-5" />
                </div>
                <div className="flex-1 pt-1">
                  <p className="font-semibold">{step.title}</p>
                  <p className="text-sm text-muted-foreground">{step.description}</p>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
