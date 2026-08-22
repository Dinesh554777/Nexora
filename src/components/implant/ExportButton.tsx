import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Download } from 'lucide-react';
import { ExportDialog } from './ExportDialog';
import { ExportData } from '@/types';

interface ExportButtonProps {
  disabled?: boolean;
  exportData: ExportData;
}

export function ExportButton({ disabled = false, exportData }: ExportButtonProps) {
  const [dialogOpen, setDialogOpen] = useState(false);

  return (
    <>
      <Button
        variant="outline"
        onClick={() => setDialogOpen(true)}
        disabled={disabled}
        className="gap-2"
      >
        <Download className="h-4 w-4" />
        Export Analysis
      </Button>

      <ExportDialog
        isOpen={dialogOpen}
        onClose={() => setDialogOpen(false)}
        exportData={exportData}
      />
    </>
  );
}
