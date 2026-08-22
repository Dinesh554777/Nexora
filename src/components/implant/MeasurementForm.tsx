import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { PatientMeasurements } from '@/types';

interface MeasurementFormProps {
  onAnalyze: (measurements: PatientMeasurements) => void;
  onClear: () => void;
  loading?: boolean;
}

export function MeasurementForm({ onAnalyze, onClear, loading }: MeasurementFormProps) {
  const [measurements, setMeasurements] = useState<PatientMeasurements>({
    femurWidth: 0,
    femurAP: 0,
    tibiaWidth: 0,
    tibiaAP: 0,
  });

  const handleChange = (field: keyof PatientMeasurements, value: string) => {
    setMeasurements(prev => ({
      ...prev,
      [field]: parseFloat(value) || 0
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onAnalyze(measurements);
  };

  const handleClear = () => {
    setMeasurements({
      femurWidth: 0,
      femurAP: 0,
      tibiaWidth: 0,
      tibiaAP: 0,
    });
    onClear();
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Patient Measurements</CardTitle>
        <CardDescription>Enter knee measurements for implant sizing</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="femurWidth">Femur Width (mm)</Label>
            <Input
              id="femurWidth"
              type="number"
              step="0.1"
              placeholder="e.g., 65.5"
              value={measurements.femurWidth || ''}
              onChange={(e) => handleChange('femurWidth', e.target.value)}
              required
            />
            <p className="text-xs text-muted-foreground">Medial-lateral femur dimension</p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="femurAP">Femur AP (mm)</Label>
            <Input
              id="femurAP"
              type="number"
              step="0.1"
              placeholder="e.g., 58.2"
              value={measurements.femurAP || ''}
              onChange={(e) => handleChange('femurAP', e.target.value)}
              required
            />
            <p className="text-xs text-muted-foreground">Anterior-posterior femur dimension</p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="tibiaWidth">Tibia Width (mm)</Label>
            <Input
              id="tibiaWidth"
              type="number"
              step="0.1"
              placeholder="e.g., 72.3"
              value={measurements.tibiaWidth || ''}
              onChange={(e) => handleChange('tibiaWidth', e.target.value)}
              required
            />
            <p className="text-xs text-muted-foreground">Medial-lateral tibia dimension</p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="tibiaAP">Tibia AP (mm)</Label>
            <Input
              id="tibiaAP"
              type="number"
              step="0.1"
              placeholder="e.g., 48.7"
              value={measurements.tibiaAP || ''}
              onChange={(e) => handleChange('tibiaAP', e.target.value)}
              required
            />
            <p className="text-xs text-muted-foreground">Anterior-posterior tibia dimension</p>
          </div>

          <div className="flex gap-3 pt-4">
            <Button type="submit" disabled={loading} className="flex-1">
              {loading ? 'Analyzing...' : 'Analyze Measurements'}
            </Button>
            <Button type="button" variant="outline" onClick={handleClear}>
              Clear
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
