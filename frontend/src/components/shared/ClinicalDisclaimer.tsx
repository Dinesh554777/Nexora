import { Info } from 'lucide-react';

export function ClinicalDisclaimer() {
  return (
    <div className="flex items-start gap-3 p-4 rounded-lg bg-muted/50 border border-muted">
      <Info className="h-5 w-5 text-muted-foreground mt-0.5 flex-shrink-0" />
      <div className="flex-1">
        <p className="text-sm text-muted-foreground leading-relaxed">
          <strong className="text-foreground">Clinical Disclaimer:</strong> AI-generated results are intended 
          for clinical decision support and should be reviewed by a qualified healthcare professional. 
          This system does not provide medical diagnoses or treatment recommendations.
        </p>
      </div>
    </div>
  );
}
