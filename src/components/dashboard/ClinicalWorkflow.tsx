import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { User, Ruler, Brain, CheckCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

const workflowSteps = [
  {
    icon: User,
    title: 'Patient Assessment',
    description: 'Capture patient demographics and clinical data',
  },
  {
    icon: Ruler,
    title: 'Knee Measurement',
    description: 'Precise measurement of femur and tibia dimensions',
  },
  {
    icon: Brain,
    title: 'AI Analysis',
    description: 'Machine learning-powered implant matching',
  },
  {
    icon: CheckCircle,
    title: 'Implant Recommendation',
    description: 'Ranked implant options with confidence scores',
  },
];

export function ClinicalWorkflow() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Clinical Workflow</CardTitle>
        <CardDescription>End-to-end AI-assisted implant planning process</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {workflowSteps.map((step, index) => {
            const Icon = step.icon;
            return (
              <div key={index} className="relative">
                <div className="flex flex-col items-center text-center space-y-3">
                  <div className={cn(
                    "rounded-full p-4 transition-colors",
                    "bg-primary/10 text-primary"
                  )}>
                    <Icon className="h-6 w-6" />
                  </div>
                  <div>
                    <h3 className="font-semibold mb-1">{step.title}</h3>
                    <p className="text-xs text-muted-foreground">{step.description}</p>
                  </div>
                </div>
                {index < workflowSteps.length - 1 && (
                  <div className="hidden lg:block absolute top-8 left-full w-full h-0.5 bg-border -translate-x-1/2" />
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
