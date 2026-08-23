import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorRetryProps {
  title?: string;
  message: string;
  onRetry: () => void;
}

export function ErrorRetry({ 
  title = 'Error', 
  message, 
  onRetry 
}: ErrorRetryProps) {
  return (
    <Alert variant="destructive">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>{title}</AlertTitle>
      <AlertDescription className="mt-2 space-y-3">
        <p>{message}</p>
        <Button 
          variant="outline" 
          size="sm" 
          onClick={onRetry}
          className="gap-2"
        >
          <RefreshCw className="h-4 w-4" />
          Try Again
        </Button>
      </AlertDescription>
    </Alert>
  );
}
