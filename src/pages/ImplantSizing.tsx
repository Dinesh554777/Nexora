import { useState } from 'react';
import { PageHeader } from '@/components/shared/PageHeader';
import { MeasurementForm } from '@/components/implant/MeasurementForm';
import { ImplantRecommendation } from '@/components/implant/ImplantRecommendation';
import { AlternativeMatches } from '@/components/implant/AlternativeMatches';
import { PatientMeasurements, ImplantRecommendation as ImplantRec } from '@/types';

export function ImplantSizing() {
  const [loading, setLoading] = useState(false);
  const [recommendation, setRecommendation] = useState<ImplantRec | null>(null);
  const [alternatives, setAlternatives] = useState<ImplantRec[]>([]);

  const handleAnalyze = (measurements: PatientMeasurements) => {
    setLoading(true);

    // Simulate API call with demo data
    setTimeout(() => {
      // Generate demo recommendation based on measurements
      const avgMeasurement = (measurements.femurWidth + measurements.femurAP + measurements.tibiaWidth + measurements.tibiaAP) / 4;
      
      const demoRecommendation: ImplantRec = {
        implantId: 'IMP-2024-A7',
        implantName: 'Genesis II Total Knee System',
        size: avgMeasurement > 60 ? 'Large' : avgMeasurement > 50 ? 'Medium' : 'Small',
        matchScore: 94,
        confidence: 92,
        measurementDifference: 0.8,
      };

      const demoAlternatives: ImplantRec[] = [
        {
          implantId: 'IMP-2024-B3',
          implantName: 'Attune Knee System',
          size: avgMeasurement > 60 ? 'Large' : avgMeasurement > 50 ? 'Medium' : 'Small',
          matchScore: 88,
          confidence: 85,
          measurementDifference: 1.5,
          rank: 2,
        },
        {
          implantId: 'IMP-2024-C5',
          implantName: 'NexGen LPS-Flex',
          size: avgMeasurement > 60 ? 'Large' : avgMeasurement > 50 ? 'Medium' : 'Small',
          matchScore: 82,
          confidence: 79,
          measurementDifference: 2.3,
          rank: 3,
        },
      ];

      setRecommendation(demoRecommendation);
      setAlternatives(demoAlternatives);
      setLoading(false);
    }, 1500);
  };

  const handleClear = () => {
    setRecommendation(null);
    setAlternatives([]);
  };

  return (
    <div className="space-y-8">
      <PageHeader
        title="Implant Sizing"
        description="AI-powered knee implant recommendation based on patient measurements"
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <div>
          <MeasurementForm
            onAnalyze={handleAnalyze}
            onClear={handleClear}
            loading={loading}
          />
        </div>

        <div className="space-y-6">
          <ImplantRecommendation recommendation={recommendation} />
          {alternatives.length > 0 && <AlternativeMatches alternatives={alternatives} />}
        </div>
      </div>
    </div>
  );
}
