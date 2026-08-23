import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle } from 'lucide-react';

export function ClinicalReview() {
  return (
    <Alert className="border-orange-200 bg-orange-50 dark:bg-orange-950 dark:border-orange-900">
      <div className="flex items-start gap-3">
        <AlertTriangle className="h-5 w-5 text-orange-600 dark:text-orange-400 mt-0.5" />
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <AlertTitle className="text-orange-800 dark:text-orange-200">
              Clinical Review Required
            </AlertTitle>
            <Badge variant="outline" className="border-orange-600 text-orange-700">
              Review Required
            </Badge>
          </div>
          <AlertDescription className="text-orange-700 dark:text-orange-300">
            AI-generated recommendations are intended to support clinical decision-making. 
            Final implant selection must be reviewed by a qualified healthcare professional 
            considering patient history, surgical planning, and clinical judgment.
          </AlertDescription>
        </div>
      </div>
    </Alert>
  );
}
