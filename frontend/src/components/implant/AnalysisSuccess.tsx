import { CheckCircle } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

export function AnalysisSuccess() {
  return (
    <Alert className="border-green-200 bg-green-50 dark:bg-green-950 dark:border-green-900">
      <CheckCircle className="h-4 w-4 text-green-600 dark:text-green-400" />
      <AlertTitle className="text-green-800 dark:text-green-200">AI Analysis Complete</AlertTitle>
      <AlertDescription className="text-green-700 dark:text-green-300">
        Knee measurements have been analyzed successfully. Review the recommended implant and alternatives below.
      </AlertDescription>
    </Alert>
  );
}
