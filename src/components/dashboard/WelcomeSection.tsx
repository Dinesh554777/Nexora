import { useNavigate } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Activity, BarChart3, ArrowRight } from 'lucide-react';

export function WelcomeSection() {
  const navigate = useNavigate();

  return (
    <Card className="border-2 border-primary/20 bg-gradient-to-br from-primary/5 to-background">
      <CardContent className="p-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex-1 space-y-4">
            <div className="flex items-center gap-3">
              <div className="rounded-full bg-primary/10 p-3">
                <Activity className="h-8 w-8 text-primary" />
              </div>
              <div>
                <h2 className="text-3xl font-bold">KneeVision AI</h2>
                <p className="text-muted-foreground">AI-Powered Orthopedic Analysis Platform</p>
              </div>
            </div>
            <p className="text-lg">
              Advanced AI-assisted knee imaging and implant planning for clinical decision support
            </p>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-3">
            <Button 
              size="lg"
              onClick={() => navigate('/implant-sizing')}
              className="gap-2"
            >
              Start Implant Analysis
              <ArrowRight className="h-4 w-4" />
            </Button>
            <Button 
              size="lg"
              variant="outline"
              onClick={() => navigate('/oa-analytics')}
              className="gap-2"
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
