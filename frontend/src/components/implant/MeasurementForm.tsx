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

interface ValidationErrors {
  femurWidth?: string;
  femurAP?: string;
  tibiaWidth?: string;
  tibiaAP?: string;
}

export function MeasurementForm({ onAnalyze, onClear, loading }: MeasurementFormProps) {
  const [measurements, setMeasurements] = useState<PatientMeasurements>({
    femurWidth: 0,
    femurAP: 0,
    tibiaWidth: 0,
    tibiaAP: 0,
  });

  const [errors, setErrors] = useState<ValidationErrors>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});

  const validateField = (_field: keyof PatientMeasurements, value: number): string | undefined => {
    if (!value || value <= 0) {
      return 'Value must be greater than 0';
    }
    if (value > 200) {
      return 'Value seems unrealistically high';
    }
    return undefined;
  };

  const handleChange = (field: keyof PatientMeasurements, value: string) => {
    const numValue = parseFloat(value) || 0;
    setMeasurements(prev => ({
      ...prev,
      [field]: numValue
    }));

    // Always validate on change
    const error = validateField(field, numValue);
    setErrors(prev => {
      const newErrors = { ...prev };
      if (error) {
        newErrors[field] = error;
      } else {
        delete newErrors[field]; // Remove error if field is now valid
      }
      return newErrors;
    });
  };

  const handleBlur = (field: keyof PatientMeasurements) => {
    setTouched(prev => ({ ...prev, [field]: true }));
    const error = validateField(field, measurements[field]);
    setErrors(prev => {
      const newErrors = { ...prev };
      if (error) {
        newErrors[field] = error;
      } else {
        delete newErrors[field]; // Remove error if field is valid
      }
      return newErrors;
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Validate all fields
    const newErrors: ValidationErrors = {};
    let hasErrors = false;

    (Object.keys(measurements) as Array<keyof PatientMeasurements>).forEach(field => {
      const error = validateField(field, measurements[field]);
      if (error) {
        newErrors[field] = error;
        hasErrors = true;
      }
    });

    setErrors(newErrors);
    setTouched({
      femurWidth: true,
      femurAP: true,
      tibiaWidth: true,
      tibiaAP: true,
    });

    if (!hasErrors) {
      onAnalyze(measurements);
    }
  };

  const handleClear = () => {
    setMeasurements({
      femurWidth: 0,
      femurAP: 0,
      tibiaWidth: 0,
      tibiaAP: 0,
    });
    setErrors({});
    setTouched({});
    onClear();
  };

  const isFormValid = 
    measurements.femurWidth > 0 &&
    measurements.femurAP > 0 &&
    measurements.tibiaWidth > 0 &&
    measurements.tibiaAP > 0 &&
    measurements.femurWidth <= 200 &&
    measurements.femurAP <= 200 &&
    measurements.tibiaWidth <= 200 &&
    measurements.tibiaAP <= 200;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Patient Measurements</CardTitle>
        <CardDescription>Enter knee measurements for implant sizing</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="femurWidth">Femur Width (mm) *</Label>
            <Input
              id="femurWidth"
              type="number"
              step="0.1"
              min="0"
              placeholder="e.g., 65.5"
              value={measurements.femurWidth || ''}
              onChange={(e) => handleChange('femurWidth', e.target.value)}
              onBlur={() => handleBlur('femurWidth')}
              className={errors.femurWidth && touched.femurWidth ? 'border-destructive' : ''}
              required
            />
            {errors.femurWidth && touched.femurWidth && (
              <p className="text-xs text-destructive">{errors.femurWidth}</p>
            )}
            <p className="text-xs text-muted-foreground">Medial-lateral femur dimension</p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="femurAP">Femur AP (mm) *</Label>
            <Input
              id="femurAP"
              type="number"
              step="0.1"
              min="0"
              placeholder="e.g., 58.2"
              value={measurements.femurAP || ''}
              onChange={(e) => handleChange('femurAP', e.target.value)}
              onBlur={() => handleBlur('femurAP')}
              className={errors.femurAP && touched.femurAP ? 'border-destructive' : ''}
              required
            />
            {errors.femurAP && touched.femurAP && (
              <p className="text-xs text-destructive">{errors.femurAP}</p>
            )}
            <p className="text-xs text-muted-foreground">Anterior-posterior femur dimension</p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="tibiaWidth">Tibia Width (mm) *</Label>
            <Input
              id="tibiaWidth"
              type="number"
              step="0.1"
              min="0"
              placeholder="e.g., 72.3"
              value={measurements.tibiaWidth || ''}
              onChange={(e) => handleChange('tibiaWidth', e.target.value)}
              onBlur={() => handleBlur('tibiaWidth')}
              className={errors.tibiaWidth && touched.tibiaWidth ? 'border-destructive' : ''}
              required
            />
            {errors.tibiaWidth && touched.tibiaWidth && (
              <p className="text-xs text-destructive">{errors.tibiaWidth}</p>
            )}
            <p className="text-xs text-muted-foreground">Medial-lateral tibia dimension</p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="tibiaAP">Tibia AP (mm) *</Label>
            <Input
              id="tibiaAP"
              type="number"
              step="0.1"
              min="0"
              placeholder="e.g., 48.7"
              value={measurements.tibiaAP || ''}
              onChange={(e) => handleChange('tibiaAP', e.target.value)}
              onBlur={() => handleBlur('tibiaAP')}
              className={errors.tibiaAP && touched.tibiaAP ? 'border-destructive' : ''}
              required
            />
            {errors.tibiaAP && touched.tibiaAP && (
              <p className="text-xs text-destructive">{errors.tibiaAP}</p>
            )}
            <p className="text-xs text-muted-foreground">Anterior-posterior tibia dimension</p>
          </div>

          <div className="flex gap-3 pt-4">
            <Button type="submit" disabled={loading || !isFormValid} className="flex-1">
              {loading ? 'Analyzing...' : 'Analyze Measurements'}
            </Button>
            <Button type="button" variant="outline" onClick={handleClear} disabled={loading}>
              Clear
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
