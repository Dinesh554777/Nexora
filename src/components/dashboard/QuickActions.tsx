import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Ruler, BarChart3, Users } from 'lucide-react';

export function QuickActions() {
  const navigate = useNavigate();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Quick Actions</CardTitle>
        <CardDescription>Access key features</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-wrap gap-3">
        <Button onClick={() => navigate('/implant-sizing')} className="flex items-center gap-2">
          <Ruler className="h-4 w-4" />
          New Implant Analysis
        </Button>
        <Button variant="outline" onClick={() => navigate('/oa-analytics')} className="flex items-center gap-2">
          <BarChart3 className="h-4 w-4" />
          View OA Analytics
        </Button>
        <Button variant="outline" className="flex items-center gap-2">
          <Users className="h-4 w-4" />
          View Patient Data
        </Button>
      </CardContent>
    </Card>
  );
}
