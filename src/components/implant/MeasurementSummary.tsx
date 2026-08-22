import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Ruler } from 'lucide-react';
import { PatientMeasurements } from '@/types';

interface MeasurementSummaryProps {
  measurements: PatientMeasurements;
}

export function MeasurementSummary({ measurements }: MeasurementSummaryProps) {
  const measurementItems = [
    { label: 'Femur Width', value: measurements.femurWidth },
    { label: 'Femur AP', value: measurements.femurAP },
    { label: 'Tibia Width', value: measurements.tibiaWidth },
    { label: 'Tibia AP', value: measurements.tibiaAP },
  ];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Ruler className="h-5 w-5 text-primary" />
          <CardTitle>Input Measurements</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          {measurementItems.map((item) => (
            <div key={item.label} className="border rounded-lg p-3 bg-muted/30">
              <p className="text-sm text-muted-foreground mb-1">{item.label}</p>
              <p className="text-2xl font-bold">{item.value.toFixed(1)} <span className="text-sm font-normal text-muted-foreground">mm</span></p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
